# 5. Booking Lifecycle Flow

## Overview
The VahanOne booking lifecycle orchestrates customer reservations from creation through vehicle conflict checking, dispatch, odometer execution, financial calculation, and invoice generation.

```mermaid
stateDiagram-v2
    [*] --> BookingDraft: Customer requests travel
    
    state BookingCreation {
        BookingDraft --> ConflictCheck: System asserts Vehicle & Date Range
        ConflictCheck --> OverlapDetected: Overlapping Booking OR Maintenance Window
        OverlapDetected --> [*]: Abort with HTTP 409 Conflict
        ConflictCheck --> BookingConfirmed: Vehicle Available & Customer Verified
    }

    BookingConfirmed --> VehicleCalendarBlocked: Calendar event created (type: booking)
    VehicleCalendarBlocked --> TripCreated: Trip initiated with start_km & Package
    
    state TripExecution {
        TripCreated --> TripOngoing: Driver Dispatched (POST /trips/{id}/start)
        TripOngoing --> InTransit: Vehicle on route (Fuel / Toll / Bata logged)
        InTransit --> TripCompletionRequest: Trip Arrives at Destination
        TripCompletionRequest --> ValidateOdometer: Submit end_km (must be >= start_km)
        ValidateOdometer --> ComputeFinancials: Extra KM, Extra Hours, Night Charges, Tolls
        ComputeFinancials --> TripCompleted: Status marked 'completed'
    }

    state InvoiceSettlement {
        TripCompleted --> RecalculateProfit: Profit Engine updates trip_profit_summary
        TripCompleted --> GenerateInvoice: Invoice created (subtotal + GST - advances)
        GenerateInvoice --> InvoiceSent: Invoiced to Customer (Status: sent)
        InvoiceSent --> PaymentRecorded: Payment added (Status: paid)
        PaymentRecorded --> [*]
    }
```

## Detailed Lifecycle Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Dispatcher as Fleet Dispatcher
    participant BookingSvc as Booking Service
    participant VehicleSvc as Vehicle Service
    participant TripSvc as Trip Service
    participant ProfitSvc as Profit Engine
    participant InvoiceSvc as Invoice Service
    participant DB as PostgreSQL

    Dispatcher->>BookingSvc: create_booking_service(vehicle_id, dates, customer)
    BookingSvc->>VehicleSvc: check_vehicle_availability_service()
    Note over VehicleSvc: Checks overlapping bookings AND maintenance_schedule
    VehicleSvc-->>BookingSvc: Available (True)
    BookingSvc->>DB: INSERT INTO bookings, vehicle_calendar_events
    
    Dispatcher->>TripSvc: create_trip_service(booking_id, package_id, start_km)
    TripSvc->>DB: INSERT INTO trips (status: 'pending')
    
    Dispatcher->>TripSvc: start_trip_service(trip_id)
    TripSvc->>DB: UPDATE trips SET status = 'ongoing', start_time = now()
    
    Dispatcher->>TripSvc: complete_trip_service(trip_id, end_km, end_time)
    TripSvc->>TripSvc: calculate_trip_financials(package, km_used, hours_used)
    TripSvc->>DB: UPDATE trips SET status = 'completed', grand_total = ...
    
    TripSvc->>ProfitSvc: recalculate_trip_profit(trip_id)
    ProfitSvc->>DB: INSERT / UPDATE trip_profit_summary
    
    Dispatcher->>InvoiceSvc: create_invoice_from_trip(trip_id)
    InvoiceSvc->>DB: INSERT INTO invoices, invoice_items
    DB-->>Dispatcher: Invoice Ready for Payment
```

## Edge Cases Handled in Code
1. **Odometer Rollback Prevention**: `end_km` must be strictly `>= start_km`, else returns `HTTP 400 Bad Request`.
2. **Duplicate Active Trip Prevention**: `_assert_no_active_trip_for_booking` prevents dispatching multiple concurrent trips for the same booking.
3. **Double Maintenance Check**: A vehicle under scheduled maintenance cannot be booked, and maintenance cannot be scheduled over an active confirmed booking.
