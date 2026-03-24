import subprocess
from typing import List, Tuple


def _run(args: List[str], timeout: int = 120) -> Tuple[int, str, str]:
    proc = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def check_docker() -> Tuple[bool, str]:
    code, out, err = _run(["docker", "version", "--format", "{{.Server.Version}}"], timeout=30)
    if code != 0:
        return False, (err or out or "docker not available").strip()
    ver = (out or "").strip() or "unknown"
    return True, ver


def pull_image(image: str) -> str:
    code, out, err = _run(["docker", "pull", image], timeout=600)
    if code != 0:
        raise RuntimeError(f"docker pull failed: {(err or out).strip()}")
    return (out or "Pull complete").strip()


def run_container(image: str, host_port: int, container_port: int, name: str | None) -> str:
    args = [
        "docker",
        "run",
        "-d",
        "-p",
        f"{host_port}:{container_port}",
    ]
    if name and name.strip():
        args.extend(["--name", name.strip()[:200]])
    args.append(image)
    code, out, err = _run(args, timeout=120)
    if code != 0:
        raise RuntimeError(f"docker run failed: {(err or out).strip()}")
    cid = (out or "").strip()
    if not cid:
        raise RuntimeError("docker run returned empty container id")
    return cid


def stop_container(container_id: str) -> str:
    code, out, err = _run(["docker", "stop", container_id], timeout=60)
    if code != 0:
        raise RuntimeError(f"docker stop failed: {(err or out).strip()}")
    return (out or "").strip()


def restart_container(container_id: str) -> str:
    code, out, err = _run(["docker", "restart", container_id], timeout=60)
    if code != 0:
        raise RuntimeError(f"docker restart failed: {(err or out).strip()}")
    return (out or "").strip()


def remove_container(container_id: str) -> str:
    code, out, err = _run(["docker", "rm", "-f", container_id], timeout=60)
    if code != 0:
        raise RuntimeError(f"docker rm failed: {(err or out).strip()}")
    return (out or "").strip()


def get_container_status(container_id: str) -> str:
    code, out, err = _run(
        [
            "docker",
            "inspect",
            "--format",
            "{{.State.Status}}",
            container_id,
        ],
        timeout=30,
    )
    if code != 0:
        raise RuntimeError(f"docker inspect failed: {(err or out).strip()}")
    return (out or "").strip()


def get_container_logs(container_id: str, lines: int = 20) -> str:
    code, out, err = _run(
        ["docker", "logs", "--tail", str(lines), container_id],
        timeout=30,
    )
    if code != 0:
        raise RuntimeError(f"docker logs failed: {(err or out).strip()}")
    return (out or err or "").strip()


def list_running() -> List[dict]:
    code, out, err = _run(
        [
            "docker",
            "ps",
            "--format",
            "{{.ID}}|{{.Image}}|{{.Ports}}|{{.Status}}",
        ],
        timeout=30,
    )
    if code != 0:
        raise RuntimeError(f"docker ps failed: {(err or out).strip()}")
    rows = []
    for line in (out or "").strip().splitlines():
        parts = line.split("|", 3)
        if len(parts) >= 4:
            rows.append(
                {
                    "id": parts[0],
                    "image": parts[1],
                    "ports": parts[2],
                    "status": parts[3],
                }
            )
    return rows
