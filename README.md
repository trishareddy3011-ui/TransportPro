# VahanOne — Transport Business Operating System & Fleet Management

**VahanOne** is a full-stack multi-tenant SaaS platform built for vehicle owners, commercial fleet operators, and transport logistics agencies. It streamlines Indian fleet compliance (RC, FC, Insurance, Permit, Pollution, Road Tax), driver dispatch, booking lifecycles, GST-compliant invoicing, real-time expense tracking, and profitability analytics.

---

## Architecture Overview

- **Backend**: FastAPI (Python 3.11+), SQLAlchemy 2.0 ORM, Alembic Migrations, Pydantic v2, APScheduler
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons
- **Database & Auth**: PostgreSQL 15+, JWT-based RBAC, Multi-Tenant Row Isolation
- **DevOps**: Docker, Docker Compose, GitHub Actions CI/CD Pipeline, Nginx SPA Reverse Proxy

---

## Default Demo Credentials

Once the stack is started, the database is automatically migrated and seeded with realistic Indian fleet demo data:

| User Role | Email | Password | Default Org ID |
| :--- | :--- | :--- | :--- |
| **Fleet Administrator** | `admin@vahanone.com` | `AdminPassword123!` | `00000000-0000-0000-0000-000000000001` |
| **Operations Manager** | `demo@vahanone.com` | `DemoPassword123!` | `00000000-0000-0000-0000-000000000001` |

---

## Quick Start with Docker (Recommended)

Docker is the primary, zero-configuration method to run VahanOne on both **Windows** and **macOS/Linux**. All environment variables have safe built-in defaults; you do not need to create or edit `.env` files to get started.

### Prerequisites

1. Install and launch **Docker Desktop**:
   - **macOS**: [Install Docker Desktop for Mac](https://docs.docker.com/desktop/setup/install/mac-install/)
   - **Windows**: [Install Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/) (Ensure WSL 2 backend is enabled)
   - **Linux**: [Install Docker Engine](https://docs.docker.com/engine/install/)

---

### Running on macOS / Linux

```bash
# 1. Clone the repository
git clone https://github.com/trishareddy3011-ui/TransportPro.git
cd TransportPro

# 2. Run the automated startup script
./start.sh
```

*(Alternatively, run `docker compose up --build`)*

---

### Running on Windows

```cmd
:: 1. Clone the repository
git clone https://github.com/trishareddy3011-ui/TransportPro.git
cd TransportPro

:: 2. Run the automated startup script (Double-click or run from CMD / PowerShell)
start.bat
```

*(Alternatively, run `docker compose up --build`)*

---

### Accessing the Local Services

Once the containers are up:
- **Frontend Application**: [http://localhost](http://localhost) (or port configured in `FRONTEND_PORT`)
- **FastAPI Backend Root**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative ReDoc Docs**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

To stop all services:
```bash
docker compose down
```

---

## Manual Local Setup (Without Docker)

### 1. PostgreSQL Setup
Ensure PostgreSQL is running locally on port `5432`:
```sql
CREATE ROLE postgres WITH SUPERUSER LOGIN PASSWORD 'postgrespassword';
CREATE DATABASE vahanone_db OWNER postgres;
```

### 2. Backend Setup

**On macOS / Linux:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python seed_demo_data.py
uvicorn app.main:app --reload --port 8000
```

**On Windows (Command Prompt / PowerShell):**
```cmd
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
python seed_demo_data.py
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup

**On macOS / Linux / Windows:**
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173).

---

## Cloud Deployment

### 1-Click Deployment via Render Blueprint
The repository includes a ready-to-deploy `render.yaml` specification:
1. Push your changes to GitHub.
2. Sign in to [Render](https://render.com/).
3. Click **New + > Blueprint** and select your `TransportPro` repository.
4. Render automatically provisions:
   - **PostgreSQL Database** (`vahanone-db`)
   - **FastAPI Backend Web Service** (`vahanone-backend`, auto-migrated & auto-seeded)
   - **React Frontend Static Site** (`vahanone-frontend` with SPA routing)
5. Click **Apply**. Your app is live in minutes!

---

## Troubleshooting & FAQ

### Port 80 or Port 8000 is already in use
- **Port 80 Conflict**: If port 80 is occupied (e.g., by IIS on Windows or local Apache), override the port in `docker-compose.yml` or run:
  ```bash
  FRONTEND_PORT=3000 docker compose up --build
  ```
  *(On Windows PowerShell: `$env:FRONTEND_PORT=3000; docker compose up --build`)*
- **Port 8000 Conflict**: Set `BACKEND_PORT=8001` in your environment.

### Docker Daemon Not Running
- If `start.sh` or `start.bat` prints `Docker daemon is not running`, open the Docker Desktop application on your machine and wait until the status indicator turns green.

### CRLF / Line Ending Issues on Windows
- A `.gitattributes` file is configured at the root to force LF endings on all scripts and Dockerfiles. If you edit shell scripts on Windows, ensure your editor preserves LF endings.

### Migrations or Database Errors
- To re-apply migrations cleanly or reset the database:
  ```bash
  docker compose down -v
  docker compose up --build
  ```

---

## Core Features

1. **Fleet & Compliance Engine**: RC, FC, Insurance, Permit, Pollution (PUC), Road Tax, and EMI tracking with automated 30/15/7-day renewal alerts.
2. **Driver & Dispatch Lifecycle**: License tracking, driver assignment, conflict checking, and duty logs.
3. **Trip & Booking Workflow**: Booking management, start/end odometer verification, allowances, and route logs.
4. **GST Invoicing**: Automated CGST/SGST/IGST tax calculation, advances, and payment tracking.
5. **Profitability Engine**: Vehicle-level and trip-level net profit analytics calculated from real revenue and operational expenses.
