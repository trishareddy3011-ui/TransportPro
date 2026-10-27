# 7. Profit Engine Flow

## Overview
The VahanOne Profit Engine bridges operational logistics with financial viability. It computes granular profitability across two orthogonal dimensions:
1. **Per-Trip Level**: Comparing realized trip billing against direct variable operating costs (fuel, tolls, driver bata, parking).
2. **Per-Vehicle Level**: Aggregating daily and monthly profit timelines to help fleet owners identify underperforming or high-maintenance vehicles.

```mermaid
flowchart TD
    subgraph RevenueInput["1. Operational Inflows (Revenue)"]
        PkgFare["Base Package Amount<br/>(e.g., Local / Outstation base)"]
        OverKm["Extra KM Revenue<br/>(Rate × Distance exceeded)"]
        OverHr["Extra Hours Revenue<br/>(Rate × Hours exceeded)"]
        DriverBata["Driver Allowance / Bata"]
        NightChg["Night Travel Charges"]
        TollBilled["Toll & State Permits Billed to Customer"]
    end

    subgraph ExpenseInput["2. Variable Operating Outflows (Expenses)"]
        FuelExp["Fuel Purchases<br/>(Diesel / CNG / Petrol receipts)"]
        TollExp["FASTag / Toll Plaza Charges"]
        ParkingExp["Parking & Entry Taxes"]
        MaintExp["En-route Maintenance / Repairs"]
        DriverBataPaid["Driver Daily Bata Disbursed"]
    end

    subgraph TripProfitEngine["3. Per-Trip Profit Calculation (recalculate_trip_profit)"]
        GrossRev["Trip Revenue = Σ(Base + Extra KM + Extra Hr + Bata + Night + Toll)"]
        TotalExp["Total Trip Expenses = Σ(Fuel + Toll + Parking + Maint + Misc)"]
        NetTripProfit["Trip Profit = Trip Revenue - Total Expenses"]
        
        PersistTrip["UPSERT into trip_profit_summary<br/>{trip_id, vehicle_id, trip_revenue, total_expense, trip_profit, date, year, month}"]
    end

    subgraph VehicleRollup["4. Vehicle-Level Rollup (_rebuild_vehicle_aggregates)"]
        RollupDaily["Aggregate by Date<br/>DELETE + INSERT INTO vehicle_daily_profit<br/>(daily revenue, expense, profit)"]
        RollupMonthly["Aggregate by Year & Month<br/>DELETE + INSERT INTO vehicle_monthly_profit<br/>(monthly performance breakdown)"]
    end

    subgraph DashboardMetrics["5. Executive Fleet Dashboard"]
        KPI1["Vehicle ROI & Margin %"]
        KPI2["Monthly Fleet Net Profit"]
        KPI3["Cost per KM (Fuel Efficiency Analysis)"]
    end

    PkgFare & OverKm & OverHr & DriverBata & NightChg & TollBilled --> GrossRev
    FuelExp & TollExp & ParkingExp & MaintExp & DriverBataPaid --> TotalExp
    GrossRev & TotalExp --> NetTripProfit
    NetTripProfit --> PersistTrip
    PersistTrip --> RollupDaily & RollupMonthly
    RollupDaily & RollupMonthly --> KPI1 & KPI2 & KPI3

    classDef rev fill:#dcfce7,stroke:#16a34a,stroke-width:2px;
    classDef exp fill:#fee2e2,stroke:#dc2626,stroke-width:2px;
    classDef calc fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    classDef rollup fill:#fef3c7,stroke:#d97706,stroke-width:2px;
    classDef kpi fill:#ede9fe,stroke:#7c3aed,stroke-width:2px;

    class PkgFare,OverKm,OverHr,DriverBata,NightChg,TollBilled,GrossRev rev;
    class FuelExp,TollExp,ParkingExp,MaintExp,DriverBataPaid,TotalExp exp;
    class NetTripProfit,PersistTrip calc;
    class RollupDaily,RollupMonthly rollup;
    class KPI1,KPI2,KPI3 kpi;
```

## Calculation Formulas

$$\text{Trip Revenue} = \text{Package Amount} + (\text{Extra KM} \times R_{\text{km}}) + (\text{Extra Hours} \times R_{\text{hr}}) + \text{Bata} + \text{Night} + \text{Toll}$$

$$\text{Total Expenses} = \sum \text{Fuel} + \sum \text{Toll} + \sum \text{Parking} + \sum \text{Maintenance} + \sum \text{Misc}$$

$$\text{Net Profit}_{\text{Trip}} = \text{Trip Revenue} - \text{Total Expenses}$$

$$\text{Monthly Vehicle Profit} = \sum_{i=1}^{N_{\text{trips}}} \text{Trip Profit}_i$$

## Performance & Optimization Notes
- **Instant Recalculation**: Every time a new expense is logged (`POST /expenses/`) or a trip is completed (`POST /trips/{id}/complete`), `profit_service.recalculate_trip_profit` runs synchronously within the transaction.
- **Aggregated Projections**: The system caches daily and monthly totals in `vehicle_daily_profit` and `vehicle_monthly_profit` tables. This guarantees $O(1)$ response times for the front-end monthly charts without scanning millions of individual trip records.
