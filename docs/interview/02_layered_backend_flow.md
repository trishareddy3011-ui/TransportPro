# 2. Layered Backend Flow

## Overview
VahanOne enforces a strict clean separation of concerns in the backend:
`HTTP Request -> Router -> Pydantic Schema Validation -> Service Layer (Business Logic & Conflicts) -> Repository / ORM -> Database Engine -> Response Model`.

Below is a detailed trace of a real core endpoint: `POST /bookings/` (Creating a new vehicle booking).

```mermaid
sequenceDiagram
    autonumber
    actor Client as Frontend Client
    participant Router as Router<br/>(routers/bookings.py)
    participant Dep as Dependencies<br/>(core/dependencies.py)
    participant Schema as Schema Validator<br/>(schemas/booking.py)
    participant Service as Business Service<br/>(services/booking_service.py)
    participant Repo as DB Models & Queries<br/>(models.py & SQLAlchemy)
    participant DB as PostgreSQL Database

    Client->>Router: POST /bookings/ (JSON payload, Bearer Token)
    
    activate Router
    Router->>Dep: get_current_user() & require_roles("admin", "member")
    activate Dep
    Dep->>Dep: Validate JWT, check token expiration & parse org_id
    Dep-->>Router: Authenticated User Object
    decrement Dep

    Router->>Schema: Validate BookingCreate payload
    activate Schema
    Schema->>Schema: Validate date range (start_date < end_date), amount >= 0
    Schema-->>Router: Validated Pydantic DTO
    deactivate Schema

    Router->>Service: create_booking_service(db, current_user, payload)
    activate Service

    Note over Service: 1. Customer-first Check
    Service->>Repo: Lookup customer or auto-create Customer record
    Repo->>DB: SELECT / INSERT INTO customers
    DB-->>Repo: Customer ID

    Note over Service: 2. Vehicle Availability & Conflict Detection
    Service->>Repo: Query overlapping active bookings for vehicle_id
    Repo->>DB: SELECT FROM bookings WHERE vehicle_id = :id AND status != 'cancelled'
    DB-->>Repo: Existing schedules

    Service->>Repo: Query overlapping maintenance schedule for vehicle_id
    Repo->>DB: SELECT FROM maintenance_schedule WHERE vehicle_id = :id
    DB-->>Repo: Maintenance windows

    alt Conflict Detected
        Service-->>Router: Raise HTTPException(400, "Vehicle is already booked or under maintenance")
        Router-->>Client: 400 Bad Request
    else No Conflict
        Note over Service: 3. Create Booking & Audit Log
        Service->>Repo: Instantiate Booking(organization_id=user.org_id, ...)
        Repo->>DB: INSERT INTO bookings ... RETURNING id
        DB-->>Repo: New Booking Row
        
        Service->>Repo: Create VehicleCalendarEvent & AuditLog
        Repo->>DB: INSERT INTO vehicle_calendar_events ...
        Repo->>DB: INSERT INTO audit_logs ...
        
        Service-->>Router: Booking ORM instance
        deactivate Service

        Router->>Schema: BookingResponse.from_orm(booking)
        activate Schema
        Schema-->>Router: JSON Serialization
        deactivate Schema

        Router-->>Client: 201 Created + JSON Response
    end
    deactivate Router
```

## Architectural Highlights
- **Fail-Fast Validation**: Pydantic validates data types, date relationships, and negative numbers before any database connection is exercised.
- **Tenant Context Injection**: `organization_id` is never trusted from the client payload for data mutation; it is pulled directly from the validated JWT token inside the dependency layer.
- **Encapsulated Business Invariants**: Complex business rules (like checking driver availability and preventing scheduling during maintenance windows) reside strictly in `booking_service.py`, leaving routers thin and testable.
