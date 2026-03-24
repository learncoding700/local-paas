<div align="center">

<h1>🚀 Local Container Deployment System</h1>
<p><em>A mini Platform-as-a-Service for your local machine</em></p>

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![Tests](https://img.shields.io/badge/Tests-25%20passing-brightgreen?style=flat-square&logo=pytest&logoColor=white)](./tests)
[![CI](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)](./.github/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](./LICENSE)

<br/>

> Deploy, monitor, and manage Docker containers from a clean web UI — all on your own machine.

</div>

---

## What It Does

**Local Container Deployment System** is a self-hosted mini-PaaS that lets authenticated users pull and run Docker images, manage container lifecycles, and observe system metrics — all through a REST API and browser dashboard.

Think of it as a lightweight Portainer or Railway, built from scratch to demonstrate end-to-end full-stack + DevOps engineering.

**Key capabilities:**
- 🔐 **JWT-secured API** — register, login, and manage containers with token-based auth
- 🐳 **Container lifecycle control** — deploy, list, stop, restart, and remove containers
- 📊 **Live observability** — Prometheus scrapes `/metrics`; Grafana ships a pre-provisioned dashboard
- 🗄️ **Persistent history** — all deployments recorded in PostgreSQL and kept in sync with Docker state
- ⚙️ **One-command setup** — single `docker compose up` brings up all six services
- ✅ **25 automated tests** — health, auth, deploy lifecycle, and security validation, run in CI

---

## Architecture

```
Browser ──► Nginx :80 (reverse proxy)
                │
      ┌─────────┼──────────┐
      ▼         ▼          ▼
  Frontend   Backend    (Docker Engine)
  (static)  (FastAPI)       ▲
                │           │ docker.sock
           PostgreSQL        │
                ▲           │
           Prometheus ───────┘
                │
            Grafana :3000
```

Six containerised roles communicate over a private Compose network. The backend talks to the host Docker daemon via a bind-mounted socket.

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| API | Python / FastAPI | 3.12 / 0.111 |
| Database | PostgreSQL | 16 |
| Auth | JWT (`python-jose`) + bcrypt | 3.3 / 1.7 |
| Containers | Docker Compose v2 | — |
| Reverse Proxy | Nginx | 1.25 |
| Metrics | Prometheus | 2.51 |
| Dashboards | Grafana | 10.4 |
| Frontend | HTML5 / CSS3 / Vanilla JS | — |
| Testing | pytest + httpx | 8.2 |
| CI | GitHub Actions | — |

---

## Quick Start

**Prerequisites:** Docker Desktop (or Docker Engine + Compose v2) running on your machine.

```bash
git clone https://github.com/your-username/mca-local-paas
cd mca-local-paas
docker compose up --build -d
```

Open **http://localhost** — the dashboard is live.

| Service | URL | Credentials |
|---|---|---|
| Web Dashboard | http://localhost | `admin` / `admin123` |
| API Docs (Swagger) | http://localhost/api/docs | — |
| Prometheus | http://localhost:9090 | — |
| Grafana | http://localhost:3000 | `admin` / `admin` |

> The `admin` dashboard user is seeded automatically on first startup.

---

## API Reference

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | — | API, DB, and Docker health check |
| `GET` | `/stats` | — | Deployment counts + host metrics |
| `GET` | `/metrics` | — | Prometheus exposition format |
| `POST` | `/auth/register` | — | Register a new user |
| `POST` | `/auth/login` | — | Obtain JWT token |
| `POST` | `/deploy` | Bearer | Pull image, run container, record to DB |
| `GET` | `/containers` | Bearer | List containers, sync with Docker state |
| `GET` | `/containers/{id}` | Bearer | Container detail + last logs |
| `POST` | `/stop` | Bearer | Stop a running container |
| `POST` | `/restart` | Bearer | Restart a container |
| `DELETE` | `/remove` | Bearer | Force-remove container + delete DB row |

Full interactive docs at **`/api/docs`** (Swagger UI) and **`/api/redoc`**.

---

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest ../tests/ -v
```

Expected output: `25 passed`.

Tests are split across four files:

| File | What it covers | External deps |
|---|---|---|
| `test_health.py` | Public endpoints, health checks | SQLite + mocks |
| `test_security.py` | Input validation, injection guards | SQLite + mocks |
| `test_auth.py` | Register, login, token flow | PostgreSQL (CI) |
| `test_deploy.py` | Full deploy lifecycle | PostgreSQL + mocked Docker CLI |

---

## CI/CD Pipeline

Four sequential GitHub Actions jobs on every push:

```
lint → unit-and-mock-tests → auth-and-deploy-tests → build-verify
```

1. **lint** — `flake8` style check + `bandit -ll` security scan on `backend/`
2. **unit-and-mock-tests** — health and security tests with SQLite, no external services needed
3. **auth-and-deploy-tests** — spins up a Postgres 16 service container, runs auth and deploy tests with Docker CLI mocked via `conftest.py`
4. **build-verify** — validates `docker compose config` and builds the backend image end-to-end

---

## Project Structure

```
mca-local-paas/
├── backend/             # FastAPI app (main.py, auth, models, docker_service…)
├── frontend/            # Static HTML/CSS/JS dashboard
├── tests/               # pytest suite (25 tests)
├── nginx/               # Reverse proxy config
├── prometheus/          # Scrape config
├── grafana/             # Provisioned datasource + dashboard JSON
├── .github/workflows/   # CI pipeline
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Security Notes

- All mutating and listing routes require a **Bearer JWT**
- Passwords are **bcrypt-hashed** before storage
- Image names are **validated** before being passed to the Docker CLI
- Default credentials are for **local/lab use only** — rotate `JWT_SECRET_KEY` and Grafana secrets before any networked deployment

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Port 80 already in use | Change the Nginx host port in `docker-compose.yml` to e.g. `"8080:80"` |
| `permission denied` on Docker socket | Add your user to the `docker` group (Linux), or ensure Docker Desktop is running (Windows/macOS) |
| Backend can't connect to Postgres | Wait for the Postgres healthcheck to pass; verify `DATABASE_URL` matches your Compose credentials |
| Tests fail with DB errors | Run from `backend/`; local runs use SQLite by default, CI uses Postgres when `CI=true` |

---

## License

[MIT](./LICENSE) — free for academic submission and personal use.
