# 9. Frontend Architecture & Flow

## Overview
The VahanOne user interface is built as a single-page application (SPA) with **React 18**, **Vite**, **TypeScript**, and **Tailwind CSS**. It emphasizes responsive, low-latency fleet operations, optimistic client updates, token refresh management, and defensive error boundaries.

```mermaid
flowchart TD
    subgraph Browser["1. Client Initialization"]
        IndexHTML["index.html (Entrypoint)"] --> MainTSX["main.tsx (ReactDOM.createRoot)"]
        MainTSX --> Router["BrowserRouter (React Router v6)"]
        Router --> AppComp["App.tsx"]
    end

    subgraph RouteDispatch["2. Routing & Shell Layout"]
        AppComp --> RouteCheck{"location.pathname<br/>isAuthPage?"}
        RouteCheck -->|"Yes (/login, /signup)"| AuthPages["Auth Container<br/>(Login.tsx / Signup.tsx)"]
        RouteCheck -->|"No (App Routes)"| AppShell["App Shell Container<br/>(Sidebar Navigation + Topbar)"]
        
        AppShell --> Pages["Page Routing"]
        Pages --> P1["/dashboard (Dashboard.tsx)"]
        Pages --> P2["/vehicles (Vehicles.tsx)"]
        Pages --> P3["/drivers (Drivers.tsx)"]
        Pages --> P4["/bookings (Bookings.tsx)"]
        Pages --> P5["/calendar (Calendar.tsx)"]
        Pages --> P6["/dispatch (Dispatch.tsx)"]
        Pages --> P7["/expenses (Expenses.tsx)"]
        Pages --> P8["/profit (Profit.tsx)"]
        Pages --> P9["/invoices (Invoices.tsx)"]
        Pages --> P10["/renewals (Renewals.tsx)"]
    end

    subgraph StateHooks["3. Hooks & State Layer"]
        P1 --> UseDash["useDashboard()<br/>Aggregates vehicle counts, active trips, reminders, cash flow"]
        AppShell --> UseAuth["useAuth()<br/>Auth state, role checks, session persistence, logout()"]
    end

    subgraph ApiServiceLayer["4. API & Data Access Layer"]
        UseDash --> DashSvc["dashboardService.ts"]
        Pages --> DomainSvcs["Domain Services<br/>(vehicleService, tripService, bookingService, invoiceService)"]
        
        DashSvc & DomainSvcs --> AxiosClient["Axios HTTP Client (lib/api.ts)"]
        DashSvc & DomainSvcs --> SupaClient["Supabase JS Client (lib/supabase.ts)"]
    end

    subgraph Interceptors["5. Axios Token Interceptor & Auto-Refresh"]
        AxiosClient --> ReqInterceptor["Request Interceptor:<br/>Inject Authorization: Bearer <accessToken>"]
        ReqInterceptor --> NetworkReq["HTTP Request to FastAPI Backend"]
        NetworkReq --> RespInterceptor{"Response Status"}
        RespInterceptor -->|"200 OK"| ReturnData["Deliver typed data to page state"]
        RespInterceptor -->|"401 Unauthorized"| RefreshQueue["Queue Requests & Trigger POST /auth/refresh<br/>using stored refresh_token"]
        RefreshQueue -->|"Success"| SaveNewTokens["Save new tokens & replay queued requests"]
        RefreshQueue -->|"Failed"| ForceLogout["clearAuthStorage() & redirect to /login"]
    end

    classDef browser fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    classDef layout fill:#fef3c7,stroke:#d97706,stroke-width:2px;
    classDef hooks fill:#dcfce7,stroke:#16a34a,stroke-width:2px;
    classDef api fill:#ede9fe,stroke:#7c3aed,stroke-width:2px;
    classDef net fill:#fee2e2,stroke:#dc2626,stroke-width:2px;

    class IndexHTML,MainTSX,Router,AppComp browser;
    class RouteCheck,AuthPages,AppShell,Pages,P1,P2,P3,P4,P5,P6,P7,P8,P9,P10 layout;
    class UseDash,UseAuth hooks;
    class DashSvc,DomainSvcs,AxiosClient,SupaClient api;
    class ReqInterceptor,NetworkReq,RespInterceptor,ReturnData,RefreshQueue,SaveNewTokens,ForceLogout net;
```

## State Management & Invariants
1. **No External Redux Overhead**: Local and custom hook state (`useState`, `useEffect`, `useCallback`) is used to keep bundle size small and render times instantaneous.
2. **Silent Refresh Interceptor**: `lib/api.ts` implements a subscriber queue (`subscribeTokenRefresh` and `onRefreshed`). If multiple parallel requests fail with `401`, only a single `POST /auth/refresh` is dispatched; upon resolution, all waiting requests retry seamlessly without user disruption.
3. **Dual Protocol Compatibility**: Frontend can communicate directly with FastAPI REST endpoints (`/bookings`, `/trips`) as well as the Supabase compatibility endpoints (`/rest/v1/*`), allowing seamless interoperability regardless of deployment target.
