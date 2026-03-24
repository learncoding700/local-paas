import time
from contextlib import asynccontextmanager
from datetime import datetime

import psutil
from fastapi import Body, Depends, FastAPI, HTTPException, Request
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from sqlalchemy import text
from sqlalchemy.orm import Session

import docker_service
from auth import get_current_user, hash_password, router as auth_router
from database import Base, SessionLocal, engine, get_db
from models import Deployment, User
from schemas import (
    ContainerActionRequest,
    ContainerDetailResponse,
    ContainerListItem,
    DeployRequest,
    DeployResponse,
    HealthResponse,
    MessageResponse,
    StatsResponse,
)
from utils import get_local_ip, get_next_port, validate_image_name

APP_NAME = "Local Container-Based Application Deployment System with Monitoring and CI/CD"
APP_VERSION = "1.0.0"
START_TIME = time.time()

api_requests_total = Counter(
    "api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status"],
)
api_request_latency_seconds = Histogram(
    "api_request_latency_seconds",
    "API request latency",
    ["endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)
deployed_containers_total = Gauge(
    "deployed_containers_total",
    "Number of deployments in running state (DB synced)",
)
system_cpu_percent = Gauge("system_cpu_percent", "Host CPU usage percent")
system_memory_percent = Gauge("system_memory_percent", "Host memory usage percent")
system_disk_percent = Gauge("system_disk_percent", "Host disk usage percent")


def _normalize_endpoint(path: str) -> str:
    parts = path.strip("/").split("/")
    if not parts or parts == [""]:
        return "/"
    out = []
    for p in parts:
        if len(p) > 20 and all(c in "0123456789abcdef" for c in p.lower()):
            out.append("{id}")
        else:
            out.append(p)
    return "/" + "/".join(out)


def _refresh_gauges_from_system():
    try:
        system_cpu_percent.set(psutil.cpu_percent(interval=None))
    except Exception:
        system_cpu_percent.set(0.0)
    try:
        vm = psutil.virtual_memory()
        system_memory_percent.set(float(vm.percent))
    except Exception:
        system_memory_percent.set(0.0)
    try:
        du = psutil.disk_usage("/")
        system_disk_percent.set(float(du.percent))
    except Exception:
        system_disk_percent.set(0.0)


def _sync_running_gauge(db: Session):
    running = db.query(Deployment).filter(Deployment.status == "running").count()
    deployed_containers_total.set(running)


def _seed_default_admin():
    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == "admin").first() is None:
            db.add(
                User(
                    username="admin",
                    hashed_password=hash_password("admin123"),
                )
            )
            db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _seed_default_admin()
    yield


import os
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    lifespan=lifespan,
    root_path=os.getenv("ROOT_PATH", ""),
)
app.include_router(auth_router)


@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    ep = _normalize_endpoint(request.url.path)
    status_code = getattr(response, "status_code", 200)
    api_requests_total.labels(
        method=request.method,
        endpoint=ep,
        status=str(status_code),
    ).inc()
    api_request_latency_seconds.labels(endpoint=ep).observe(elapsed)
    return response


@app.get("/", tags=["root"])
def root():
    uptime_s = int(time.time() - START_TIME)
    try:
        cpu = float(psutil.cpu_percent(interval=None))
    except Exception:
        cpu = 0.0
    try:
        mem = float(psutil.virtual_memory().percent)
    except Exception:
        mem = 0.0
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "uptime_seconds": uptime_s,
        "cpu_percent": round(cpu, 1),
        "memory_percent": round(mem, 1),
    }


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health(db: Session = Depends(get_db)):
    api_ok = "ok"
    db_ok = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = "error"
    docker_ok, docker_ver = docker_service.check_docker()
    docker_str = f"ok (docker {docker_ver})" if docker_ok else f"error ({docker_ver})"
    overall = (
        "healthy"
        if db_ok == "ok" and docker_ok
        else "degraded"
    )
    return HealthResponse(status=overall, api=api_ok, database=db_ok, docker=docker_str)


@app.get("/stats", response_model=StatsResponse, tags=["stats"])
def stats(db: Session = Depends(get_db)):
    total = db.query(Deployment).count()
    running = db.query(Deployment).filter(Deployment.status == "running").count()
    stopped = db.query(Deployment).filter(Deployment.status == "stopped").count()
    _refresh_gauges_from_system()
    _sync_running_gauge(db)
    cpu = float(system_cpu_percent._value.get())  # noqa: SLF001
    mem = float(system_memory_percent._value.get())  # noqa: SLF001
    disk = float(system_disk_percent._value.get())  # noqa: SLF001
    return StatsResponse(
        total_deployments=total,
        running=running,
        stopped=stopped,
        cpu_percent=round(cpu, 1),
        memory_percent=round(mem, 1),
        disk_percent=round(disk, 1),
        local_ip=get_local_ip(),
    )


@app.get("/metrics", tags=["metrics"])
def metrics():
    db = SessionLocal()
    try:
        _refresh_gauges_from_system()
        _sync_running_gauge(db)
    finally:
        db.close()
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@app.post("/deploy", response_model=DeployResponse, tags=["deploy"])
def deploy(
    body: DeployRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not validate_image_name(body.image):
        raise HTTPException(status_code=400, detail="Invalid image name")

    used = [r[0] for r in db.query(Deployment.host_port).all()]
    try:
        host_port = get_next_port(used)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    try:
        docker_service.pull_image(body.image.strip())
        cid = docker_service.run_container(
            body.image.strip(),
            host_port,
            body.container_port,
            body.name,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    time.sleep(3)

    try:
        st = docker_service.get_container_status(cid)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    if st != "running":
        try:
            logs = docker_service.get_container_logs(cid, lines=50)
        except RuntimeError:
            logs = "Could not fetch logs"
        raise HTTPException(
            status_code=500,
            detail={"message": "Container did not reach running state", "logs": logs},
        )

    dep = Deployment(
        container_id=cid,
        image=body.image.strip(),
        name=body.name,
        host_port=host_port,
        container_port=body.container_port,
        status="running",
    )
    db.add(dep)
    db.commit()
    db.refresh(dep)
    _sync_running_gauge(db)

    url = f"http://{get_local_ip()}:{host_port}"
    return DeployResponse(
        container_id=dep.container_id,
        image=dep.image,
        name=dep.name,
        host_port=dep.host_port,
        container_port=dep.container_port,
        url=url,
        status=dep.status,
        created_at=dep.created_at,
    )


@app.get("/containers", response_model=list[ContainerListItem], tags=["containers"])
def list_containers(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    items = db.query(Deployment).order_by(Deployment.created_at.desc()).all()
    local_ip = get_local_ip()
    for d in items:
        try:
            st = docker_service.get_container_status(d.container_id)
            mapped = "running" if st == "running" else "stopped" if st in ("exited", "dead") else st
            if mapped != d.status:
                d.status = mapped
                if mapped == "stopped" and d.stopped_at is None:
                    d.stopped_at = datetime.utcnow()
                if mapped == "running":
                    d.stopped_at = None
        except RuntimeError:
            pass
    db.commit()
    _sync_running_gauge(db)
    return [
        ContainerListItem(
            container_id=d.container_id,
            image=d.image,
            name=d.name,
            host_port=d.host_port,
            container_port=d.container_port,
            status=d.status,
            created_at=d.created_at,
            stopped_at=d.stopped_at,
            url=f"http://{local_ip}:{d.host_port}",
        )
        for d in items
    ]


@app.get("/containers/{container_id}", response_model=ContainerDetailResponse, tags=["containers"])
def get_container(
    container_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    d = db.query(Deployment).filter(Deployment.container_id == container_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Deployment not found")
    try:
        logs = docker_service.get_container_logs(container_id, lines=20)
    except RuntimeError:
        logs = ""
    local_ip = get_local_ip()
    return ContainerDetailResponse(
        container_id=d.container_id,
        image=d.image,
        name=d.name,
        host_port=d.host_port,
        container_port=d.container_port,
        status=d.status,
        created_at=d.created_at,
        stopped_at=d.stopped_at,
        url=f"http://{local_ip}:{d.host_port}",
        logs=logs,
    )


@app.post("/stop", response_model=MessageResponse, tags=["containers"])
def stop_container_route(
    body: ContainerActionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    d = db.query(Deployment).filter(Deployment.container_id == body.container_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Deployment not found")
    try:
        docker_service.stop_container(body.container_id)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    d.status = "stopped"
    d.stopped_at = datetime.utcnow()
    db.commit()
    _sync_running_gauge(db)
    return MessageResponse(message="Container stopped")


@app.post("/restart", response_model=MessageResponse, tags=["containers"])
def restart_container_route(
    body: ContainerActionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    d = db.query(Deployment).filter(Deployment.container_id == body.container_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Deployment not found")
    try:
        docker_service.restart_container(body.container_id)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    d.status = "running"
    d.stopped_at = None
    db.commit()
    _sync_running_gauge(db)
    return MessageResponse(message="Container restarted")


@app.delete("/remove", response_model=MessageResponse, tags=["containers"])
def remove_container_route(
    body: ContainerActionRequest = Body(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    d = db.query(Deployment).filter(Deployment.container_id == body.container_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Deployment not found")
    try:
        docker_service.remove_container(body.container_id)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    db.delete(d)
    db.commit()
    _sync_running_gauge(db)
    return MessageResponse(message="Container removed")
