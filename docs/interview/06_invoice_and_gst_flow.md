# 6. Invoice & GST Flow

## Overview
VahanOne provides an automated invoicing and tax calculation engine tailored to Indian transport logistics. It transforms completed trips into GST-compliant invoices with line items, deductions for advance payments, and payment state machines.

```mermaid
flowchart TD
    subgraph Trigger["1. Invoicing Trigger"]
        CompletedTrip["Completed Trip<br/>(status: 'completed', distance_km, extras logged)"]
        BookingDirect["Direct Booking<br/>(Flat rate booking without meter)"]
    end

    subgraph TaxEngine["2. Line Item & Tax Calculation"]
        BaseItem["Base Fare / Package Amount<br/>(e.g., 8hr / 80km package)"]
        ExtrasItem["Extra Charges<br/>- Extra KM & Extra Hours<br/>- Driver Bata<br/>- Night Charges<br/>- Toll & Parking"]
        Subtotal["Subtotal = Base + Extras"]
        
        GSTDecision{"Tax Classification"}
        GSTDecision -->|"Intra-State (Same State)"| SplitGST["CGST 6% + SGST 6% (Total 12%)<br/>or CGST 2.5% + SGST 2.5% (5% GTA)"]
        GSTDecision -->|"Inter-State"| IGST["IGST 12% / 5%"]
        
        TotalCalc["Total Amount = Subtotal + Tax Amount"]
        AdvanceDeduct["Balance Due = Total Amount - Advance Received"]
    end

    subgraph InvoicingPersistence["3. Storage & State Machine"]
        GenInvNum["Generate Sequential Invoice Number<br/>(e.g., 10001, 10002... per organization)"]
        InsertInv["INSERT INTO invoices<br/>(status: 'draft')"]
        InsertItems["INSERT INTO invoice_items<br/>(line_total_cents stored in BigInt)"]
    end

    subgraph PaymentLifecycle["4. Payment Lifecycle"]
        DraftState["Status: DRAFT<br/>(Editable line items, rates)"] -->|"Send to Customer"| SentState["Status: SENT<br/>(Awaiting settlement)"]
        SentState -->|"Record Payment (Cents)"| CheckFull{"Balance == 0?"}
        CheckFull -->|"No (Partial)"| SentState
        CheckFull -->|"Yes (Fully Paid)"| PaidState["Status: PAID<br/>(Immutable, Locked against changes)"]
        SentState -->|"Due Date Exceeded"| OverdueState["Status: OVERDUE<br/>(Triggers collections alert)"]
    end

    CompletedTrip --> BaseItem & ExtrasItem
    BookingDirect --> BaseItem
    BaseItem & ExtrasItem --> Subtotal
    Subtotal --> GSTDecision
    SplitGST & IGST --> TotalCalc
    TotalCalc --> AdvanceDeduct
    AdvanceDeduct --> GenInvNum
    GenInvNum --> InsertInv --> InsertItems
    InsertItems --> DraftState

    classDef trigger fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    classDef calc fill:#fef3c7,stroke:#d97706,stroke-width:2px;
    classDef persist fill:#dcfce7,stroke:#16a34a,stroke-width:2px;
    classDef pay fill:#ede9fe,stroke:#7c3aed,stroke-width:2px;

    class CompletedTrip,BookingDirect trigger;
    class BaseItem,ExtrasItem,Subtotal,SplitGST,IGST,TotalCalc,AdvanceDeduct calc;
    class GenInvNum,InsertInv,InsertItems persist;
    class DraftState,SentState,PaidState,OverdueState pay;
```

## Mathematical Formulae

$$\text{Subtotal} = \text{Package Amount} + (\text{Extra KM} \times \text{Rate}) + (\text{Extra Hours} \times \text{Rate}) + \text{Driver Bata} + \text{Toll} + \text{Night Charges}$$

$$\text{Total Invoice Amount} = \text{Subtotal} + \text{Tax Amount}$$

$$\text{Balance Due} = \text{Total Invoice Amount} - \text{Advance Received}$$

## Security & Concurrency Highlights
1. **Invoice Number Gap Prevention**: Sequential generation queries existing non-deleted numbers for the organization, finding the lowest available sequential index starting from `10001`.
2. **Double-Invoicing Guard**: A Unique Constraint on `(organization_id, trip_id)` and an explicit application check prevent multiple invoices against the same trip.
3. **Immutability of Settled Invoices**: Once status transitions to `PAID`, all `PUT /invoices/{id}` updates are blocked with `HTTP 400 Bad Request`.
