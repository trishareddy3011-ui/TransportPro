# 10. CI/CD & Deployment Pipeline

## Overview
The VahanOne deployment lifecycle ensures that every commit pushed to GitHub is automatically linted, type-checked, tested, built, containerized, and deployed to production cloud infrastructure with zero downtime.

```mermaid
flowchart TD
    subgraph Developer["1. Local Development"]
        Dev["Developer working locally<br/>(start.sh / start.bat / Docker Compose)"]
        GitCommit["git commit -m 'feat: ...'"]
        GitPush["git push origin main"]
        Dev --> GitCommit --> GitPush
    end

    subgraph GitHubActions["2. GitHub Actions CI (.github/workflows/ci.yml)"]
        GitPush --> TriggerCI["Trigger on push to main / deploy-ready"]
        
        subgraph BackendJob["Backend CI (Python 3.11)"]
            PySetup["Set up Python 3.11 & Pip Cache"]
            FlakeLint["Flake8 Code Linting"]
            PytestSuite["Pytest Test Suite (66 tests)<br/>(In-memory SQLite isolation)"]
            PySetup --> FlakeLint --> PytestSuite
        end

        subgraph FrontendJob["Frontend CI (Node 18/20)"]
            NodeSetup["Set up Node & NPM Cache"]
            TypeCheck["TypeScript Strict Check (tsc --noEmit)"]
            ViteBuild["Production Build (vite build)"]
            NodeSetup --> TypeCheck --> ViteBuild
        end

        TriggerCI --> BackendJob & FrontendJob
    end

    subgraph CloudDeploy["3. Render Cloud Deployment (render.yaml Blueprint)"]
        ViteBuild & PytestSuite -->|"CI Passes (Green)"| RenderWebhook["Render Auto-Deploy Webhook"]
        
        subgraph ProvisionDB["Postgres Database (vahanone-db)"]
            PGInit["Spin up PostgreSQL 15 Instance"]
        end

        subgraph DeployBackend["Backend Web Service (vahanone-backend)"]
            PullBackend["Pull backend/ code & pip install"]
            AutoMigrate["alembic upgrade head<br/>(Apply database migrations)"]
            AutoSeed["python seed_demo_data.py<br/>(Seed Indian test fleet)"]
            RunUvicorn["uvicorn app.main:app --port $PORT<br/>(Start ASGI Web Server)"]
            PullBackend --> AutoMigrate --> AutoSeed --> RunUvicorn
        end

        subgraph DeployFrontend["Frontend Static Site (vahanone-frontend)"]
            PullFrontend["Pull frontend/ code & npm install"]
            BuildDist["npm run build -> dist/"]
            NginxEdge["Render CDN / Edge Hosting<br/>(SPA Rewrites: /* -> /index.html)"]
            PullFrontend --> BuildDist --> NginxEdge
        end

        RenderWebhook --> ProvisionDB
        ProvisionDB --> DeployBackend
        DeployBackend --> DeployFrontend
    end

    subgraph LiveUsers["4. Live Public URL Access"]
        DeployFrontend --> PublicApp["https://vahanone-frontend.onrender.com"]
        DeployBackend --> PublicDocs["https://vahanone-backend.onrender.com/docs"]
    end

    classDef dev fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    classDef ci fill:#fef3c7,stroke:#d97706,stroke-width:2px;
    classDef cloud fill:#dcfce7,stroke:#16a34a,stroke-width:2px;
    classDef live fill:#ede9fe,stroke:#7c3aed,stroke-width:2px;

    class Dev,GitCommit,GitPush dev;
    class TriggerCI,PySetup,FlakeLint,PytestSuite,NodeSetup,TypeCheck,ViteBuild ci;
    class RenderWebhook,PGInit,PullBackend,AutoMigrate,AutoSeed,RunUvicorn,PullFrontend,BuildDist,NginxEdge cloud;
    class PublicApp,PublicDocs live;
```

## Production Pipeline Stages
1. **Linting & Hygiene**: `flake8` enforces PEP8 formatting rules and catches undefined symbols and circular imports before any deployment begins.
2. **Type Safety Verification**: `tsc --noEmit` verifies strict TypeScript typing across all components, interfaces, and API responses.
3. **Database Migration Synchronization**: Database schema changes are version-controlled via Alembic revisions (`alembic/versions/`). During container boot or Render deployment, `alembic upgrade head` runs automatically before the web server begins accepting HTTP traffic.
4. **Zero-Downtime Deployment**: Render creates the new container instances, waits for HTTP `GET /` to return `200 OK`, and then swaps the DNS router to the new container without dropping in-flight client requests.
