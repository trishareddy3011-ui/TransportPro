# VahanOne — Cloud Production Deployment Guide

This guide details how to deploy **VahanOne** online with a public link:
- **Database**: PostgreSQL (Render Managed Postgres, Neon, or Supabase)
- **Backend API & Reminder Scheduler**: Render (Python Web Service)
- **Frontend SPA Application**: Render (Static Site) or Vercel

---

## Method 1: Render 1-Click Blueprint (Recommended)

Render Blueprints configure the PostgreSQL database, the FastAPI backend, and the React frontend in a single coordinated deployment using `render.yaml`.

### Step-by-Step Instructions:
1. Log into your account at [Render](https://render.com/).
2. On your Render dashboard, click **New +** in the top-right and select **Blueprint**.
3. Connect your GitHub repository:
   ```
   https://github.com/trishareddy3011-ui/TransportPro.git
   ```
4. Render will inspect `render.yaml` and display the blueprint plan:
   - **`vahanone-db`**: Free PostgreSQL database
   - **`vahanone-backend`**: Python web service with automatic Alembic migrations and demo seeding
   - **`vahanone-frontend`**: React static site with SPA redirect rules
5. Click **Apply**.
6. Wait 3–4 minutes for the services to build:
   - Render provisions the database first.
   - The backend runs `alembic upgrade head` and `python seed_demo_data.py`, then starts Uvicorn.
   - The frontend builds the static assets with `npm run build` and points to the backend.
7. Once completed, your public URLs will be displayed on the Render dashboard:
   - **Frontend URL**: `https://vahanone-frontend.onrender.com`
   - **Backend API Docs**: `https://vahanone-backend.onrender.com/docs`

---

## Method 2: Manual Web Service on Render + Frontend on Vercel

If you prefer to host the frontend on **Vercel** and the backend on **Render**:

### Step 1: Deploy Database & Backend on Render
1. Create a PostgreSQL database on Render:
   - Name: `vahanone-db`
   - Database: `vahanone_db`
   - User: `vahanone_user`
   - Plan: `Free`
2. Create a Web Service for the backend:
   - Root Directory: `backend`
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `sh -c "alembic upgrade head && python seed_demo_data.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT"`
   - Add Environment Variables:
     | Key | Value / Source |
     | :--- | :--- |
     | `DATABASE_URL` | *Copy Connection String from `vahanone-db`* |
     | `JWT_SECRET_KEY` | *Click 'Generate' or enter 32+ random characters* |
     | `JWT_ALGORITHM` | `HS256` |
     | `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` |
     | `ENABLE_REMINDER_SCHEDULER` | `true` |
     | `SEED_DEMO_DATA` | `true` |
     | `CORS_ORIGINS` | `*` |
3. Deploy and copy your backend URL (e.g. `https://vahanone-backend.onrender.com`).

### Step 2: Deploy Frontend on Vercel
1. Log into [Vercel](https://vercel.com/) and click **Add New > Project**.
2. Select your repository `TransportPro`.
3. In the project settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
4. Expand **Environment Variables**:
   | Key | Value |
   | :--- | :--- |
   | `VITE_API_BASE_URL` | `https://vahanone-backend.onrender.com` |
   | `VITE_SUPABASE_URL` | `https://vahanone-backend.onrender.com` |
   | `VITE_SUPABASE_ANON_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.production_token` |
5. Click **Deploy**.

---

## Verification & Smoke Test

1. Open your live frontend URL.
2. Verify you can log in with:
   - **Email**: `admin@vahanone.com`
   - **Password**: `AdminPassword123!`
3. Verify that vehicles, drivers, bookings, invoices, and expenses load on the dashboard.
4. Open `<your-backend-url>/docs` and test endpoints interactively.
