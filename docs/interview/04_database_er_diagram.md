# 4. Database Entity-Relationship (ER) Diagram

## Overview
VahanOne operates on a normalized PostgreSQL schema with 27 relational tables. Core entities derive from three architectural base mixins:
- `TimestampMixin`: `created_at`, `updated_at` (automatic UTC timestamps)
- `TenantMixin`: `organization_id` (UUID foreign reference isolating every record)
- `SoftDeleteMixin`: `deleted_at` (preserving audit history on customers, vehicles, drivers)

```mermaid
erDiagram
    ORGANIZATIONS ||--o{ USERS : "employs"
    ORGANIZATIONS ||--o{ ROLES : "defines"
    ROLES ||--o{ USER_ROLES : "assigned_in"
    USERS ||--o{ USER_ROLES : "has"
    ROLES ||--o{ ROLE_PERMISSIONS : "contains"
    PERMISSIONS ||--o{ ROLE_PERMISSIONS : "mapped_in"

    ORGANIZATIONS ||--o{ CUSTOMERS : "owns"
    ORGANIZATIONS ||--o{ VEHICLES : "owns"
    ORGANIZATIONS ||--o{ DRIVERS : "employs"
    ORGANIZATIONS ||--o{ TRIP_PACKAGES : "configures"

    CUSTOMERS ||--o{ BOOKINGS : "places"
    VEHICLES ||--o{ BOOKINGS : "allocated_to"
    DRIVERS ||--o{ BOOKINGS : "assigned_to"

    VEHICLES ||--o{ MAINTENANCE_SCHEDULE : "undergoes"
    VEHICLES ||--o{ VEHICLE_CALENDAR_EVENTS : "scheduled_in"
    BOOKINGS ||--o{ VEHICLE_CALENDAR_EVENTS : "spawns"
    MAINTENANCE_SCHEDULE ||--o| VEHICLE_CALENDAR_EVENTS : "blocks"

    BOOKINGS ||--o{ TRIPS : "executed_via"
    VEHICLES ||--o{ TRIPS : "travels"
    TRIP_PACKAGES ||--o{ TRIPS : "billed_under"

    TRIPS ||--o{ EXPENSES : "incurs"
    BOOKINGS ||--o{ EXPENSES : "attributed_to"
    VEHICLES ||--o{ EXPENSES : "charged_to"

    TRIPS ||--o| TRIP_PROFIT_SUMMARY : "generates"
    VEHICLES ||--o{ TRIP_PROFIT_SUMMARY : "recorded_for"
    VEHICLES ||--o{ VEHICLE_DAILY_PROFIT : "aggregates_daily"
    VEHICLES ||--o{ VEHICLE_MONTHLY_PROFIT : "aggregates_monthly"

    CUSTOMERS ||--o{ INVOICES : "billed_to"
    TRIPS ||--o| INVOICES : "finalized_as"
    BOOKINGS ||--o{ INVOICES : "originates_from"
    INVOICES ||--o{ INVOICE_ITEMS : "contains"
    INVOICES ||--o{ PAYMENTS : "collected_via"

    REMINDER_RULES ||--o{ REMINDERS : "triggers"
    REMINDERS ||--o{ NOTIFICATION_EVENTS : "dispatches"

    ORGANIZATIONS {
        uuid id PK
        string name UK
        boolean is_active
    }

    USERS {
        uuid id PK
        uuid organization_id FK
        string email
        string hashed_password
        boolean is_active
        boolean is_superuser
        int refresh_token_version
    }

    CUSTOMERS {
        bigint id PK
        uuid organization_id FK
        string customer_name
        string company
        string phone_number
        string gst_number
        string city
        string state
    }

    VEHICLES {
        bigint id PK
        uuid organization_id FK
        string vehicle_number UK
        string vehicle_type
        string fuel_type
        timestamp insurance_expiry_date
        timestamp permit_expiry_date
        timestamp fc_expiry_date
        timestamp pollution_expiry_date
        timestamp road_tax_expiry_date
        timestamp service_due_date
        numeric emi_amount
        int emi_due_day
    }

    DRIVERS {
        bigint id PK
        uuid organization_id FK
        string name
        string license_number UK
        timestamp license_expiry
        string contact_number
    }

    BOOKINGS {
        bigint id PK
        uuid organization_id FK
        bigint customer_id FK
        bigint vehicle_id FK
        bigint driver_id FK
        string pickup_location
        string destination
        timestamp start_date
        timestamp end_date
        numeric booking_amount
        string status
    }

    TRIPS {
        bigint id PK
        uuid organization_id FK
        bigint booking_id FK
        bigint vehicle_id FK
        bigint package_id FK
        bigint start_km
        bigint end_km
        numeric distance_km
        numeric extra_km_amount
        numeric driver_bata
        numeric toll_amount
        numeric advance_received
        numeric grand_total
        numeric trip_revenue
        string status
    }

    EXPENSES {
        bigint id PK
        uuid organization_id FK
        bigint trip_id FK
        bigint booking_id FK
        bigint vehicle_id FK
        enum category
        numeric amount
        timestamp expense_date
    }

    TRIP_PROFIT_SUMMARY {
        bigint id PK
        uuid organization_id FK
        bigint trip_id FK
        bigint vehicle_id FK
        numeric trip_revenue
        numeric total_expense
        numeric trip_profit
        date profit_date
        int year
        int month
    }

    INVOICES {
        bigint id PK
        uuid organization_id FK
        bigint customer_id FK
        bigint trip_id FK
        bigint booking_id FK
        string invoice_number UK
        timestamp invoice_date
        numeric subtotal
        numeric tax_amount
        numeric total_amount
        numeric advance_received
        string status
    }

    PAYMENTS {
        bigint id PK
        uuid organization_id FK
        bigint invoice_id FK
        bigint amount_cents
        string method
        string transaction_ref
    }

    REMINDER_RULES {
        bigint id PK
        uuid organization_id FK
        string name
        string category
        string event_type
        int trigger_days_before
        int priority
    }

    REMINDERS {
        bigint id PK
        uuid organization_id FK
        bigint rule_id FK
        string entity_type
        bigint entity_id
        timestamp reminder_date
        timestamp due_date
        string status
        string message
    }
```

## Key Schema Design Decisions
1. **Financial Integrity**: Money amounts in Invoices, Trips, and Expenses use `Numeric(12, 2)` for precision, while Payment transactions use `BigInteger amount_cents` to eliminate floating-point rounding errors.
2. **Double Linkage (Bookings & Trips)**: An Invoice links to both `customer_id` and optional `trip_id` / `booking_id`. This allows invoicing ad-hoc direct bookings as well as multi-leg trip contracts.
3. **Soft Deletions**: Deleting a vehicle or driver preserves historical booking and trip revenue calculations via `deleted_at IS NULL` query filters.
