# 8. Compliance Reminder Scheduler

## Overview
VahanOne features an automated compliance and document expiry monitoring engine. It protects transport operators against heavy regulatory fines and vehicle impoundment under the Indian Motor Vehicles Act by tracking statutory renewals (RC, FC, Insurance, National Permits, PUC, Road Tax, EMI).

> [!NOTE]
> **Code vs. README Discrepancy**: While the original README mentions `APScheduler`, the production codebase executes a dedicated Python background daemon thread (`backend/app/services/reminder_scheduler.py`) using `threading.Thread` with a configurable sleep interval (`settings.reminder_scheduler_interval_minutes = 60`), guaranteeing lightweight execution without external broker dependencies.

```mermaid
flowchart TD
    subgraph SchedulerThread["1. Background Daemon Loop (reminder_scheduler.py)"]
        StartLoop["Scheduler Started on FastAPI Boot<br/>(start_reminder_scheduler)"] --> SleepTick["Sleep Interval (default: 60 mins)"]
        SleepTick --> OpenDBSession["Open Isolated SQLAlchemy Session"]
        OpenDBSession --> FetchActiveOrgs["Query All Active Organizations<br/>(Organization.is_active == True)"]
    end

    subgraph EvaluationEngine["2. Compliance Rule Evaluation (reminder_service.py)"]
        FetchActiveOrgs --> IterateOrgs["For Each Organization UUID"]
        IterateOrgs --> LoadRules["Load Default & Custom Reminder Rules<br/>(30-day, 15-day, 7-day, 0-day thresholds)"]
        
        LoadRules --> CheckVehicles["Query Vehicles in Tenant"]
        CheckVehicles --> RuleRC["Insurance Expiry Check<br/>(insurance_expiry_date)"]
        CheckVehicles --> RuleFC["Fitness Certificate Check<br/>(fc_expiry_date)"]
        CheckVehicles --> RulePermit["Permit Expiry Check<br/>(permit_expiry_date)"]
        CheckVehicles --> RulePUC["Pollution Certificate Check<br/>(pollution_expiry_date)"]
        CheckVehicles --> RuleTax["Road Tax Check<br/>(road_tax_expiry_date)"]
        CheckVehicles --> RuleEMI["Vehicle EMI Due Check<br/>(_calculate_next_emi_due_datetime)"]
        CheckVehicles --> RuleMaint["Service & Tyre Change Due"]
    end

    subgraph DedupAndAlert["3. Deduplication & Alert Generation"]
        RuleRC & RuleFC & RulePermit & RulePUC & RuleTax & RuleEMI & RuleMaint --> EvaluateThreshold{"Current Date >= (Due Date - Threshold Days)?"}
        EvaluateThreshold -->|"No"| Ignore["Skip (Compliant)"]
        EvaluateThreshold -->|"Yes"| CheckExists{"Reminder Already Exists in DB<br/>for entity_id + due_date?"}
        CheckExists -->|"Yes"| SkipDup["Skip (Prevent Spam)"]
        CheckExists -->|"No"| CreateReminder["Create Reminder Record<br/>status: 'pending'"]
    end

    subgraph DispatchLayer["4. Notifications & UI Alerts"]
        CreateReminder --> DBReminders["INSERT INTO reminders"]
        CreateReminder --> DBNotifs["INSERT INTO notification_events<br/>(Channel: IN_APP / EMAIL / SMS)"]
        DBReminders --> UIDash["Fleet Dashboard Badge<br/>(Amber for < 30 days, Red for < 7 days)"]
    end

    classDef sched fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    classDef rules fill:#fef3c7,stroke:#d97706,stroke-width:2px;
    classDef alert fill:#fee2e2,stroke:#dc2626,stroke-width:2px;
    classDef ui fill:#dcfce7,stroke:#16a34a,stroke-width:2px;

    class StartLoop,SleepTick,OpenDBSession,FetchActiveOrgs,IterateOrgs sched;
    class LoadRules,CheckVehicles,RuleRC,RuleFC,RulePermit,RulePUC,RuleTax,RuleEMI,RuleMaint rules;
    class EvaluateThreshold,CheckExists,CreateReminder,DBReminders,DBNotifs alert;
    class UIDash ui;
```

## Compliance Threshold Matrix
| Statutory Document | Standard Indian Validity | System Warning Thresholds | Risk if Unaddressed |
| :--- | :--- | :--- | :--- |
| **Vehicle Insurance** | 1 Year (Comprehensive/Third-party) | **30 days, 15 days, 7 days** | Vehicle impounded; claims denied |
| **Fitness Certificate (FC)** | 1–2 Years (Commercial Vehicles) | **30 days, 15 days, 7 days** | Seizure of registration certificate |
| **State / National Permit** | 1–5 Years | **30 days, 15 days, 7 days** | Heavy inter-state border penalties |
| **Pollution (PUC)** | 6 Months | **15 days, 7 days, 1 day** | ₹10,000 fine under amended MV Act |
| **Road Tax** | Quarterly / Annual | **30 days, 15 days, 7 days** | Compound penalty interest |
| **Vehicle Loan EMI** | Monthly | **7 days, 3 days, Due Date** | Credit rating penalty; repossession risk |

## Deduplication Strategy
To avoid bombarding fleet managers with duplicate notifications every 60 minutes, the query explicitly checks:
```python
existing = reminder_repository.find_existing_reminder(
    db,
    organization_id=org_id,
    rule_id=rule.id,
    entity_type="vehicle",
    entity_id=vehicle.id,
    due_date=due_date
)
```
If an active or acknowledged reminder already exists for that specific due date, the scheduler idempotently skips creating another.
