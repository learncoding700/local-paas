# 🚀 Local Container Deployment System

## MCA Final Year Project

Badges:

![Python](https://img.shields.io/badge/python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)
![Tests](https://img.shields.io/badge/tests-25-brightgreen)
![Docker](https://img.shields.io/badge/docker-compose-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 1. What This Project Does

This project is a **mini local Platform-as-a-Service (PaaS)** for your own machine. It exposes a small web dashboard and REST API so authenticated users can **run pre-built Docker images** (such as `nginx` or `redis`) on automatically chosen host ports, **list and control** those containers, and **persist deployment history** in PostgreSQL. The stack adds **JWT authentication**, **Prometheus metrics**, **Grafana dashboards**, an **Nginx** entry point, and a **GitHub Actions** pipeline that lints the backend, runs **25 focused tests**, and verifies Docker images build cleanly.

## 2. Architecture

```
                    ┌─────────────┐
   Browser ────────►│   Nginx     │ :80  (API + static UI proxy)
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
      ┌──────────────┐ ┌─────────┐ ┌──────────────┐
      │   Frontend   │ │ Backend │ │  (external)  │
      │ nginx:static │ │ FastAPI │ │ Docker Engine│
      └──────────────┘ └────┬────┘ └──────▲───────┘
                            │             │
                     ┌──────▼─────┐       │ docker.sock
                     │ PostgreSQL │       │
                     └────────────┘       │
                            ▲             │
                     ┌──────┴──────┐      │
                     │ Prometheus  │◄────┘ scrape /metrics
                     └──────┬──────┘
                            │
                     ┌──────▼──────┐
                     │   Grafana   │ :3000
                     └─────────────┘
```

Six container roles: **PostgreSQL**, **Backend**, **Frontend (static Nginx)**, **Edge Nginx**, **Prometheus**, **Grafana**. The host Docker daemon runs user images; the backend talks to it via the mounted socket.

## 3. Tech Stack

| Component        | Technology              | Version   |
|-----------------|-------------------------|-----------|
| API             | Python / FastAPI        | 3.12 / 0.111 |
| DB              | PostgreSQL              | 16        |
| Auth            | JWT (python-jose), bcrypt | 3.3 / 1.7 |
| Containers      | Docker Compose v2       | —         |
| Reverse proxy   | Nginx                   | 1.25      |
| Metrics         | Prometheus              | 2.51      |
| Dashboards      | Grafana                 | 10.4      |
| Frontend        | HTML5 / CSS3 / JS       | —         |
| Tests           | pytest, httpx, mocks    | 8.2       |
| CI              | GitHub Actions          | —         |

## 4. Quick Start

```bash
git clone <your-repo-url>
cd mca-local-paas
docker compose up --build -d
```

Open **http://localhost** in a browser. The API is available under **http://localhost/api/** (e.g. **http://localhost/api/docs** for Swagger).

## 5. Default Credentials

| Area        | Username | Password  |
|------------|----------|-----------|
| Dashboard  | `admin`  | `admin123` |
| Grafana    | `admin`  | `admin`   |

The dashboard user is **created automatically** on first API startup if it does not exist. Change secrets in production via `JWT_SECRET_KEY` and Grafana env vars.

## 6. Service URLs

| Service    | URL                     | Purpose                    |
|-----------|-------------------------|----------------------------|
| Web UI    | http://localhost        | Login + dashboard          |
| API docs  | http://localhost/api/docs | Interactive OpenAPI      |
| Prometheus| http://localhost:9090   | Metrics UI                 |
| Grafana   | http://localhost:3000   | Dashboards                 |
| Backend   | (internal) backend:8000 | Scraped by Prometheus      |
| PostgreSQL| (internal) postgres:5432| Application data           |

## 7. API Endpoints

| Method | Endpoint              | Auth   | Description |
|--------|-----------------------|--------|-------------|
| GET    | `/`                   | No     | Project info + basic stats |
| GET    | `/health`             | No     | API, DB, Docker health |
| GET    | `/stats`              | No     | Deployment + host metrics |
| GET    | `/metrics`            | No     | Prometheus exposition |
| POST   | `/auth/register`      | No     | Register user |
| POST   | `/auth/login`         | No     | JWT login |
| POST   | `/deploy`             | Bearer | Pull + run image, record DB |
| GET    | `/containers`         | Bearer | List + sync status |
| GET    | `/containers/{id}`    | Bearer | Detail + last logs |
| POST   | `/stop`               | Bearer | Stop container |
| POST   | `/restart`            | Bearer | Restart container |
| DELETE | `/remove`             | Bearer | Force-remove + delete row |

## 8. Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest ../tests/ -v
```

**Expected:** `25 passed`.

Health and security tests use **SQLite** and mocks locally. On **GitHub Actions** (`CI=true`), auth and deploy jobs use the **service PostgreSQL** container with the same application code.

## 9. CI/CD Pipeline

The workflow **`.github/workflows/ci.yml`** runs four jobs in order:

1. **lint** — `flake8` on `backend/` and `bandit -ll` for basic security scanning.  
2. **unit-and-mock-tests** — installs dependencies, runs `test_health.py` and `test_security.py` (no real Docker or Postgres required).  
3. **auth-and-deploy-tests** — spins up **Postgres 16**, sets `DATABASE_URL`, runs `test_auth.py` and `test_deploy.py` with Docker **subprocess calls mocked** in `conftest.py`.  
4. **build-verify** — validates `docker compose config` and builds the backend image to ensure the Dockerfile still works.

## 10. Project Structure

```
mca-local-paas/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth.py
│   ├── docker_service.py
│   ├── utils.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html
│   ├── dashboard.html
│   ├── css/style.css
│   └── js/app.js
├── tests/
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_auth.py
│   ├── test_deploy.py
│   └── test_security.py
├── nginx/
│   └── nginx.conf
├── prometheus/
│   └── prometheus.yml
├── grafana/provisioning/
│   ├── datasources/prometheus.yml
│   └── dashboards/
│       ├── dashboard.yml
│       └── json/paas_dashboard.json
├── .github/workflows/ci.yml
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## 11. Examiner FAQ

**Q: How is this different from Docker Desktop?**  
Docker Desktop is a general container runtime UI. This project is a **narrow PaaS workflow**: authenticated API, **port allocation policy**, **persistent deployment records**, metrics, and CI tests that prove behavior.

**Q: How is the system secured?**  
**JWT** protects mutating and listing routes. Passwords are **bcrypt-hashed**. Image names are **validated** to reduce injection via the Docker CLI. The stack is intended for **local lab use**; production would add TLS, stronger secrets rotation, and RBAC.

**Q: What happens if a container crashes?**  
The next **GET `/containers`** call runs `docker inspect` and **syncs** the `status` field in PostgreSQL toward the real engine state (for example `running` vs `exited`).

**Q: Show me the tests**  
There are **25 tests** in four files: health/public endpoints, authentication, deployment lifecycle with a **mocked Docker CLI**, and **security validation** on deploy input. Run `pytest ../tests/ -v` from `backend/`.

**Q: Why this monitoring stack?**  
**Prometheus** scrapes the FastAPI `/metrics` endpoint (request counts, latency histogram, gauges for CPU/memory/disk and running deployments). **Grafana** ships a pre-provisioned **“Local PaaS Dashboard”** so you can demonstrate observability during the viva.

## 12. Troubleshooting

| Symptom | What to try |
|--------|-------------|
| **Port 80 in use** | Stop IIS/other web servers, or change the host mapping in `docker-compose.yml` for the `nginx` service (e.g. `"8080:80"`). |
| **Docker socket permission denied** | On Linux, add your user to the `docker` group or run Compose with appropriate permissions. On Windows, ensure Docker Desktop is running and WSL2 backend is healthy. |
| **Backend cannot connect to Postgres** | Wait for the `postgres` healthcheck; check `DATABASE_URL` matches `docker-compose.yml` credentials. |
| **`docker` command not found in backend container** | The compose file bind-mounts `/usr/bin/docker` from the host — this targets **Linux** hosts. On Windows, prefer Docker Desktop’s Linux engine or adjust mounts/paths for your setup. |
| **Tests failing with DB errors** | Run from `backend/` with `pip install -r requirements.txt`. For local runs, tests default to **SQLite**; CI uses Postgres when `CI=true` and `DATABASE_URL` is PostgreSQL. |

## License

MIT — suitable for academic submission; adjust if your institution requires a different license.
