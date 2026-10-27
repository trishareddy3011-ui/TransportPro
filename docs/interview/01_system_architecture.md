# 1. System Architecture

## Overview
VahanOne is structured as a decoupled three-tier multi-tenant web platform containerized with Docker and Docker Compose. It separates client-side SPA rendering, RESTful business logic and scheduling, and relational data storage.

```mermaid
graph TD
    subgraph Client["Client Browser"]
        SPA["React 18 + Vite SPA<br/>(Client-Side Routing, React Hooks, Tailwind CSS)"]
    end

    subgraph DockerCompose["Docker Compose Unified Network"]
        subgraph FrontendTier["Frontend Container (Port 80)"]
            NGINX["Nginx Web Server<br/>(Static Asset Hosting, Gzip, SPA Routing Fallback)"]
        end

        subgraph BackendTier["FastAPI Backend Container (Port 8000)"]
            Uvicorn["Uvicorn ASGI Server"]
            FastAPI["FastAPI Core App"]
            CORS["CORS Middleware"]
            AuthSec["JWT Auth & Security"]
            Routers["REST API Routers<br/>(/vehicles, /bookings, /trips, /invoices, /profits...)"]
            CompatLayer["Supabase/PostgREST Compatibility Router<br/>(/rest/v1/*, /auth/v1/*)"]
            Scheduler["APScheduler Background Service<br/>(Compliance Expiry Checks every 60m)"]
        end

        subgraph DataTier["Database Container (Port 5432)"]
            PG[("PostgreSQL 15 Database<br/>(Multi-Tenant Schema, Alembic Versioning)")]
        end
    end

    SPA -->|"HTTP / HTTPS Requests (Port 80)"| NGINX
    SPA -->|"Direct API Calls / REST (Port 8000)"| Uvicorn
    NGINX -.->|"Proxies / Distributes Static HTML/JS"| SPA
    Uvicorn --> FastAPI
    FastAPI --> CORS
    CORS --> AuthSec
    AuthSec --> Routers
    AuthSec --> CompatLayer
    Routers -->|"SQLAlchemy 2.0 ORM (psycopg)"| PG
    CompatLayer -->|"Direct Filter Translations"| PG
    Scheduler -->|"Queries Expiring Docs & EMI"| PG

    classDef clientStyle fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    classDef frontendStyle fill:#fef3c7,stroke:#d97706,stroke-width:2px;
    classDef backendStyle fill:#dcfce7,stroke:#16a34a,stroke-width:2px;
    classDef dataStyle fill:#ede9fe,stroke:#7c3aed,stroke-width:2px;

    class SPA clientStyle;
    class NGINX frontendStyle;
    class Uvicorn,FastAPI,CORS,AuthSec,Routers,CompatLayer,Scheduler backendStyle;
    class PG dataStyle;
```

## Architectural Highlights
1. **Containerized Network**: In local development and Docker Compose, services communicate over an internal bridge network (`db:5432` and `backend:8000`), with only ports 80 (Frontend) and 8000 (Backend) exposed to the host machine.
2. **Reverse Proxying**: In production Docker, Nginx acts as an HTTP server serving built SPA assets and redirecting all unhandled paths to `/index.html` to support HTML5 client-side history routing.
3. **Dual API Handling**: FastAPI handles native structured CRUD routers with Pydantic validation while concurrently serving a PostgREST-compatible translation engine (`/rest/v1/*`) to support client-side data querying without cloud dependencies.
