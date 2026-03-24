import os
import subprocess as sp
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

# Test DB: SQLite locally; Postgres in GitHub Actions when DATABASE_URL is provided.
if not (os.getenv("CI") == "true" and os.getenv("DATABASE_URL", "").startswith("postgresql")):
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-for-pytest-only-32chars")

_BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(_BACKEND))

from database import Base, engine, get_db  # noqa: E402
from main import app  # noqa: E402

SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionTesting()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def mock_docker(monkeypatch):
    monkeypatch.setattr("main.time.sleep", lambda _s: None)
    state = {"run_count": 0, "stopped": set()}

    def fake_run(args, capture_output=True, text=True, timeout=None, **kwargs):
        cmd = list(args)

        if not cmd or cmd[0] != "docker":
            return sp.CompletedProcess(cmd, 1, "", "not docker")

        if "version" in cmd:
            return sp.CompletedProcess(cmd, 0, "26.1.0\n", "")

        if "pull" in cmd:
            return sp.CompletedProcess(cmd, 0, "Pull complete", "")

        if cmd[1:2] == ["run"]:
            state["run_count"] += 1
            cid = f"abc123{state['run_count']:012d}"
            return sp.CompletedProcess(cmd, 0, cid + "\n", "")

        if "inspect" in cmd and "--format" in cmd:
            cid = cmd[-1]
            if cid in state["stopped"]:
                return sp.CompletedProcess(cmd, 0, "exited\n", "")
            return sp.CompletedProcess(cmd, 0, "running\n", "")

        if "logs" in cmd:
            return sp.CompletedProcess(cmd, 0, "log line\n", "")

        if cmd[1:2] == ["stop"]:
            cid = cmd[-1]
            state["stopped"].add(cid)
            return sp.CompletedProcess(cmd, 0, "", "")

        if cmd[1:2] == ["restart"]:
            cid = cmd[-1]
            state["stopped"].discard(cid)
            return sp.CompletedProcess(cmd, 0, "", "")

        if cmd[1:2] == ["rm"]:
            return sp.CompletedProcess(cmd, 0, "", "")

        if cmd[1:2] == ["ps"]:
            return sp.CompletedProcess(cmd, 0, "", "")

        return sp.CompletedProcess(cmd, 1, "", "unhandled docker command")

    monkeypatch.setattr("docker_service.subprocess.run", fake_run)
    return fake_run


@pytest.fixture
def auth_headers(client):
    client.post("/auth/register", json={"username": "testuser", "password": "testpass123"})
    r = client.post("/auth/login", json={"username": "testuser", "password": "testpass123"})
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def registered_user(client):
    creds = {"username": "registered_fixture_user", "password": "testpass123"}
    client.post("/auth/register", json=creds)
    return creds
