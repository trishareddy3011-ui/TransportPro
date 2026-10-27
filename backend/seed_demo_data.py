from __future__ import annotations

import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
import uuid

# Ensure backend root is in python path
sys.path.insert(0, ".")

from app.database import SessionLocal
from app.models import (
    Base,
    Booking,
    Customer,
    Driver,
    Expense,
    ExpenseCategoryEnum,
    Invoice,
    MaintenanceSchedule,
    Organization,
    Role,
    Trip,
    TripPackage,
    TripProfitSummary,
    TripStatusEnum,
    User,
    UserRole,
    Vehicle,
    VehicleCalendarEvent,
    CalendarEventTypeEnum,
)
from app.core.security import hash_password
from sqlalchemy import text


def seed():
    db = SessionLocal()
    try:
        print("Starting comprehensive demo data seeding...")

        # 1. Organization
        org_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            org = Organization(id=org_id, name="VahanOne Fleet Logistics India Pvt Ltd", is_active=True)
            db.add(org)
            db.flush()
            print(f"Created organization: {org.name}")
        else:
            org.name = "VahanOne Fleet Logistics India Pvt Ltd"
            db.flush()
            print(f"Updated organization: {org.name}")

        # 2. Roles
        admin_role = db.query(Role).filter(Role.organization_id == org_id, Role.name == "admin").first()
        if not admin_role:
            admin_role = Role(organization_id=org_id, name="admin", description="Full administrator access")
            db.add(admin_role)
            db.flush()

        # 3. Demo Users
        users_to_create = [
            ("admin@vahanone.com", "AdminPassword123!", "Fleet Administrator"),
            ("demo@vahanone.com", "DemoPassword123!", "Demo Operations Manager"),
        ]

        for email, pwd, full_name in users_to_create:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(
                    email=email,
                    hashed_password=hash_password(pwd),
                    organization_id=org_id,
                    is_active=True,
                    is_superuser=True,
                )
                db.add(user)
                db.flush()
                db.add(UserRole(user_id=user.id, role_id=admin_role.id))
                print(f"Created user: {email}")
            else:
                user.hashed_password = hash_password(pwd)
                user.organization_id = org_id
                user.is_active = True
                db.flush()
                print(f"Updated password for user: {email}")

            # Profile
            db.execute(
                text(
                    "INSERT INTO user_profiles (user_id, organization_id, full_name, role) "
                    "VALUES (:uid, :oid, :name, 'admin') "
                    "ON CONFLICT (user_id) DO UPDATE SET full_name = :name, organization_id = :oid"
                ),
                {"uid": user.id, "oid": org_id, "name": full_name},
            )

        # 4. Company Settings
        db.execute(
            text(
                "INSERT INTO company_settings (organization_id, company_name, address, city, state, pincode, phone, email, gst_number, pan_number, bank_name, bank_account_number, bank_ifsc_code, invoice_prefix) "
                "VALUES (:oid, 'VahanOne Fleet Logistics India Pvt Ltd', 'Plot 42, Sector 2, HITEC City', 'Hyderabad', 'Telangana', '500081', '+919848099887', 'billing@vahanone.com', '36AAACV1234M1Z8', 'AAACV1234M', 'HDFC Bank Ltd', '50200012345678', 'HDFC0001234', 'INV') "
                "ON CONFLICT (organization_id) DO UPDATE SET company_name = EXCLUDED.company_name, city = EXCLUDED.city, gst_number = EXCLUDED.gst_number"
            ),
            {"oid": org_id},
        )

        now = datetime.utcnow()

        # 5. Realistic Indian Vehicles
        vehicles_data = [
            {
                "vehicle_number": "TS09AB1234",
                "vehicle_type": "Mini Truck",
                "make": "Tata",
                "model": "Intra V30",
                "seating_capacity": 2,
                "fuel_type": "Diesel",
                "purchase_price": 850000.0,
                "emi_amount": 18500.0,
                "emi_due_day": 5,
                "registration_date": now - timedelta(days=730),
                "insurance_expiry_date": now + timedelta(days=25),
                "permit_expiry_date": now + timedelta(days=45),
                "fc_expiry_date": now + timedelta(days=90),
                "pollution_expiry_date": now + timedelta(days=120),
                "road_tax_expiry_date": now + timedelta(days=365),
                "is_active": True,
            },
            {
                "vehicle_number": "TS07UA5678",
                "vehicle_type": "Pickup",
                "make": "Ashok Leyland",
                "model": "Dost Strong",
                "seating_capacity": 3,
                "fuel_type": "Diesel",
                "purchase_price": 780000.0,
                "emi_amount": 16000.0,
                "emi_due_day": 10,
                "registration_date": now - timedelta(days=500),
                "insurance_expiry_date": now + timedelta(days=14),
                "permit_expiry_date": now + timedelta(days=20),
                "fc_expiry_date": now + timedelta(days=60),
                "pollution_expiry_date": now + timedelta(days=80),
                "road_tax_expiry_date": now + timedelta(days=180),
                "is_active": True,
            },
            {
                "vehicle_number": "TS08CD9012",
                "vehicle_type": "Tempo Traveller",
                "make": "Force",
                "model": "Traveller 3350",
                "seating_capacity": 17,
                "fuel_type": "Diesel",
                "purchase_price": 1650000.0,
                "emi_amount": 32000.0,
                "emi_due_day": 15,
                "registration_date": now - timedelta(days=400),
                "insurance_expiry_date": now + timedelta(days=30),
                "permit_expiry_date": now + timedelta(days=60),
                "fc_expiry_date": now + timedelta(days=15),
                "pollution_expiry_date": now + timedelta(days=180),
                "road_tax_expiry_date": now + timedelta(days=365),
                "is_active": True,
            },
            {
                "vehicle_number": "AP09EF3456",
                "vehicle_type": "Commercial Truck",
                "make": "BharatBenz",
                "model": "1217C Tipper",
                "seating_capacity": 2,
                "fuel_type": "Diesel",
                "purchase_price": 2400000.0,
                "emi_amount": 48000.0,
                "emi_due_day": 20,
                "registration_date": now - timedelta(days=900),
                "insurance_expiry_date": now + timedelta(days=8),
                "permit_expiry_date": now + timedelta(days=35),
                "fc_expiry_date": now + timedelta(days=45),
                "pollution_expiry_date": now + timedelta(days=7),
                "road_tax_expiry_date": now + timedelta(days=200),
                "is_active": True,
            },
            {
                "vehicle_number": "KA01GH7890",
                "vehicle_type": "Mini Truck",
                "make": "Tata",
                "model": "Ace Gold CNG",
                "seating_capacity": 2,
                "fuel_type": "CNG",
                "purchase_price": 560000.0,
                "emi_amount": 12000.0,
                "emi_due_day": 1,
                "registration_date": now - timedelta(days=600),
                "insurance_expiry_date": now + timedelta(days=65),
                "permit_expiry_date": now + timedelta(days=120),
                "fc_expiry_date": now + timedelta(days=180),
                "pollution_expiry_date": now + timedelta(days=90),
                "road_tax_expiry_date": now + timedelta(days=300),
                "is_active": True,
            },
            {
                "vehicle_number": "MH12XY4321",
                "vehicle_type": "Pickup Truck",
                "make": "Mahindra",
                "model": "Bolero Maxi Truck",
                "seating_capacity": 2,
                "fuel_type": "Diesel",
                "purchase_price": 820000.0,
                "emi_amount": 17500.0,
                "emi_due_day": 7,
                "registration_date": now - timedelta(days=350),
                "insurance_expiry_date": now + timedelta(days=110),
                "permit_expiry_date": now + timedelta(days=140),
                "fc_expiry_date": now + timedelta(days=220),
                "pollution_expiry_date": now + timedelta(days=150),
                "road_tax_expiry_date": now + timedelta(days=365),
                "is_active": True,
            },
        ]

        vehicles_map: dict[str, Vehicle] = {}
        for vdata in vehicles_data:
            veh = db.query(Vehicle).filter(Vehicle.organization_id == org_id, Vehicle.vehicle_number == vdata["vehicle_number"]).first()
            if not veh:
                veh = Vehicle(organization_id=org_id, **vdata)
                db.add(veh)
                db.flush()
                print(f"Created vehicle: {veh.vehicle_number}")
            else:
                for k, v in vdata.items():
                    setattr(veh, k, v)
                db.flush()
                print(f"Updated vehicle: {veh.vehicle_number}")
            vehicles_map[veh.vehicle_number] = veh

        # 6. Realistic Drivers
        drivers_data = [
            {"name": "Ramesh Goud", "license_number": "TS0920190012345", "contact_number": "+919848012345", "license_expiry": now + timedelta(days=450)},
            {"name": "Venkat Reddy", "license_number": "TS0720180054321", "contact_number": "+919848023456", "license_expiry": now + timedelta(days=320)},
            {"name": "Mohammed Rafiq", "license_number": "TS0820200098765", "contact_number": "+919848034567", "license_expiry": now + timedelta(days=180)},
            {"name": "Suresh Naidu", "license_number": "AP0920170033221", "contact_number": "+919848045678", "license_expiry": now + timedelta(days=95)},
        ]

        drivers_map: dict[str, Driver] = {}
        for ddata in drivers_data:
            drv = db.query(Driver).filter(Driver.organization_id == org_id, Driver.license_number == ddata["license_number"]).first()
            if not drv:
                drv = Driver(organization_id=org_id, **ddata)
                db.add(drv)
                db.flush()
                print(f"Created driver: {drv.name}")
            else:
                for k, v in ddata.items():
                    setattr(drv, k, v)
                db.flush()
                print(f"Updated driver: {drv.name}")
            drivers_map[drv.name] = drv

        # 7. Realistic Customers
        customers_data = [
            {
                "customer_name": "K. Venkatesh",
                "company": "Hyderabad Agro Distributors",
                "phone_number": "+919848112233",
                "email": "venkatesh@hyderabadagro.com",
                "gst_number": "36AAACH1234A1Z5",
                "city": "Hyderabad",
                "state": "Telangana",
                "address": "Godown No 14, Agriculture Market, Patancheru",
            },
            {
                "customer_name": "S. Agarwal",
                "company": "Deccan Cement & Logistics",
                "phone_number": "+919848223344",
                "email": "logistics@deccancement.com",
                "gst_number": "36AABCD5678F1Z2",
                "city": "Secunderabad",
                "state": "Telangana",
                "address": "Industrial Area, Medchal Highway",
            },
            {
                "customer_name": "Dr. Ananya Rao",
                "company": "Telangana Pharma Transport",
                "phone_number": "+919848334455",
                "email": "supplychain@telanganapharma.com",
                "gst_number": "36AABCP9012K1Z9",
                "city": "Hyderabad",
                "state": "Telangana",
                "address": "Genome Valley, Shamirpet",
            },
            {
                "customer_name": "Krishna Murthy",
                "company": "Sri Krishna Retail Mart",
                "phone_number": "+919848445566",
                "email": "murthy@krishnamart.com",
                "gst_number": "36AAECK3456L1Z1",
                "city": "Warangal",
                "state": "Telangana",
                "address": "Main Road, Hanamkonda",
            },
        ]

        customers_map: dict[str, Customer] = {}
        for cdata in customers_data:
            cust = db.query(Customer).filter(Customer.organization_id == org_id, Customer.phone_number == cdata["phone_number"]).first()
            if not cust:
                cust = Customer(organization_id=org_id, **cdata)
                db.add(cust)
                db.flush()
                print(f"Created customer: {cust.company}")
            else:
                for k, v in cdata.items():
                    setattr(cust, k, v)
                db.flush()
                print(f"Updated customer: {cust.company}")
            customers_map[cust.company] = cust

        # 8. Trip Packages
        packages_data = [
            {
                "name": "Local Industrial 8h/80km",
                "package_category": "local",
                "included_hours": 8,
                "included_km": 80,
                "base_amount": 2500.0,
                "km_rate": 14.0,
                "extra_km_rate": 14.0,
                "extra_hour_rate": 150.0,
                "driver_bata_default": 300.0,
                "active": True,
            },
            {
                "name": "Outstation Express Daily",
                "package_category": "outstation",
                "included_hours": 24,
                "included_km": 300,
                "base_amount": 6500.0,
                "km_rate": 16.0,
                "extra_km_rate": 16.0,
                "minimum_km_per_day": 300,
                "driver_bata_default": 500.0,
                "night_charge_default": 400.0,
                "active": True,
            },
            {
                "name": "Airport Cargo Dispatch",
                "package_category": "transfer",
                "included_hours": 4,
                "included_km": 50,
                "base_amount": 2200.0,
                "km_rate": 18.0,
                "extra_km_rate": 18.0,
                "extra_hour_rate": 200.0,
                "driver_bata_default": 200.0,
                "active": True,
            },
        ]

        packages_map: dict[str, TripPackage] = {}
        for pdata in packages_data:
            pkg = db.query(TripPackage).filter(TripPackage.organization_id == org_id, TripPackage.name == pdata["name"]).first()
            if not pkg:
                pkg = TripPackage(organization_id=org_id, **pdata)
                db.add(pkg)
                db.flush()
                print(f"Created package: {pkg.name}")
            else:
                for k, v in pdata.items():
                    setattr(pkg, k, v)
                db.flush()
                print(f"Updated package: {pkg.name}")
            packages_map[pkg.name] = pkg

        # 9. Bookings
        bookings_data = [
            {
                "customer_id": customers_map["Hyderabad Agro Distributors"].id,
                "customer_name": "K. Venkatesh",
                "customer_company": "Hyderabad Agro Distributors",
                "customer_phone": "+919848112233",
                "customer_email": "venkatesh@hyderabadagro.com",
                "customer_gst_number": "36AAACH1234A1Z5",
                "customer_city": "Hyderabad",
                "vehicle_id": vehicles_map["TS09AB1234"].id,
                "driver_id": drivers_map["Ramesh Goud"].id,
                "pickup_location": "Patancheru Industrial Area",
                "destination": "Shamshabad Air Cargo Complex",
                "start_date": now - timedelta(days=3),
                "end_date": now - timedelta(days=2),
                "booking_amount": 14500.0,
                "status": "completed",
            },
            {
                "customer_id": customers_map["Deccan Cement & Logistics"].id,
                "customer_name": "S. Agarwal",
                "customer_company": "Deccan Cement & Logistics",
                "customer_phone": "+919848223344",
                "customer_email": "logistics@deccancement.com",
                "customer_gst_number": "36AABCD5678F1Z2",
                "customer_city": "Secunderabad",
                "vehicle_id": vehicles_map["AP09EF3456"].id,
                "driver_id": drivers_map["Venkat Reddy"].id,
                "pickup_location": "Medchal Yard",
                "destination": "Gachibowli Financial District",
                "start_date": now - timedelta(days=2),
                "end_date": now - timedelta(days=1),
                "booking_amount": 18000.0,
                "status": "completed",
            },
            {
                "customer_id": customers_map["Telangana Pharma Transport"].id,
                "customer_name": "Dr. Ananya Rao",
                "customer_company": "Telangana Pharma Transport",
                "customer_phone": "+919848334455",
                "customer_email": "supplychain@telanganapharma.com",
                "customer_gst_number": "36AABCP9012K1Z9",
                "customer_city": "Hyderabad",
                "vehicle_id": vehicles_map["TS08CD9012"].id,
                "driver_id": drivers_map["Mohammed Rafiq"].id,
                "pickup_location": "Uppal Pharma Park",
                "destination": "Vijayawada Medical Hub",
                "start_date": now - timedelta(hours=6),
                "end_date": now + timedelta(days=2),
                "booking_amount": 26500.0,
                "status": "active",
            },
            {
                "customer_id": customers_map["Sri Krishna Retail Mart"].id,
                "customer_name": "Krishna Murthy",
                "customer_company": "Sri Krishna Retail Mart",
                "customer_phone": "+919848445566",
                "customer_email": "murthy@krishnamart.com",
                "customer_gst_number": "36AAECK3456L1Z1",
                "customer_city": "Warangal",
                "vehicle_id": vehicles_map["TS07UA5678"].id,
                "driver_id": drivers_map["Suresh Naidu"].id,
                "pickup_location": "Bowenpally Wholesale Market",
                "destination": "Warangal Main Depot",
                "start_date": now + timedelta(days=1),
                "end_date": now + timedelta(days=3),
                "booking_amount": 12000.0,
                "status": "confirmed",
            },
        ]

        created_bookings = []
        for bdata in bookings_data:
            existing_b = db.query(Booking).filter(
                Booking.organization_id == org_id,
                Booking.vehicle_id == bdata["vehicle_id"],
                Booking.pickup_location == bdata["pickup_location"],
            ).first()
            if not existing_b:
                existing_b = Booking(organization_id=org_id, **bdata)
                db.add(existing_b)
                db.flush()
                print(f"Created booking: {existing_b.pickup_location} -> {existing_b.destination}")
            else:
                for k, v in bdata.items():
                    setattr(existing_b, k, v)
                db.flush()
            created_bookings.append(existing_b)

        # 10. Trips
        trip_data = [
            {
                "booking_id": created_bookings[0].id,
                "vehicle_id": vehicles_map["TS09AB1234"].id,
                "package_id": packages_map["Local Industrial 8h/80km"].id,
                "package_name": "Local Industrial 8h/80km",
                "trip_date": (now - timedelta(days=3)).date(),
                "start_place": "Patancheru",
                "end_place": "Shamshabad",
                "start_km": 42000,
                "end_km": 42350,
                "distance_km": 350.0,
                "start_time": now - timedelta(days=3),
                "end_time": now - timedelta(days=2),
                "trip_revenue": 14500.0,
                "advance_received": 3000.0,
                "grand_total": 14500.0,
                "status": TripStatusEnum.COMPLETED,
                "notes": "Delivered agro produce safely with zero transit delay",
            },
            {
                "booking_id": created_bookings[1].id,
                "vehicle_id": vehicles_map["AP09EF3456"].id,
                "package_id": packages_map["Outstation Express Daily"].id,
                "package_name": "Outstation Express Daily",
                "trip_date": (now - timedelta(days=2)).date(),
                "start_place": "Medchal",
                "end_place": "Gachibowli",
                "start_km": 78500,
                "end_km": 78950,
                "distance_km": 450.0,
                "start_time": now - timedelta(days=2),
                "end_time": now - timedelta(days=1),
                "trip_revenue": 18000.0,
                "advance_received": 5000.0,
                "grand_total": 18000.0,
                "status": TripStatusEnum.COMPLETED,
                "notes": "Bulk cement delivery completed on schedule",
            },
            {
                "booking_id": created_bookings[2].id,
                "vehicle_id": vehicles_map["TS08CD9012"].id,
                "package_id": packages_map["Outstation Express Daily"].id,
                "package_name": "Outstation Express Daily",
                "trip_date": now.date(),
                "start_place": "Uppal",
                "end_place": "Vijayawada",
                "start_km": 25100,
                "end_km": None,
                "distance_km": 310.0,
                "start_time": now - timedelta(hours=6),
                "end_time": None,
                "trip_revenue": 26500.0,
                "advance_received": 6000.0,
                "grand_total": 26500.0,
                "status": TripStatusEnum.ONGOING,
                "notes": "Pharma shipment en route to Vijayawada hospital center",
            },
        ]

        created_trips = []
        for tdata in trip_data:
            existing_t = db.query(Trip).filter(Trip.organization_id == org_id, Trip.booking_id == tdata["booking_id"]).first()
            if not existing_t:
                existing_t = Trip(organization_id=org_id, **tdata)
                db.add(existing_t)
                db.flush()
                print(f"Created trip: {existing_t.start_place} -> {existing_t.end_place}")
            else:
                for k, v in tdata.items():
                    setattr(existing_t, k, v)
                db.flush()
            created_trips.append(existing_t)

        # 11. Expenses
        expenses_data = [
            {
                "trip_id": created_trips[0].id,
                "booking_id": created_bookings[0].id,
                "vehicle_id": vehicles_map["TS09AB1234"].id,
                "category": ExpenseCategoryEnum.FUEL,
                "amount": 4200.0,
                "fuel_amount": 4200.0,
                "total_amount": 4200.0,
                "description": "Diesel 45 Litres at HPCL Patancheru",
                "expense_date": now - timedelta(days=3),
            },
            {
                "trip_id": created_trips[0].id,
                "booking_id": created_bookings[0].id,
                "vehicle_id": vehicles_map["TS09AB1234"].id,
                "category": ExpenseCategoryEnum.TOLL,
                "amount": 750.0,
                "toll_amount": 750.0,
                "total_amount": 750.0,
                "description": "Hyderabad Outer Ring Road (ORR) Toll FASTag",
                "expense_date": now - timedelta(days=3),
            },
            {
                "trip_id": created_trips[0].id,
                "booking_id": created_bookings[0].id,
                "vehicle_id": vehicles_map["TS09AB1234"].id,
                "category": ExpenseCategoryEnum.OTHER,
                "amount": 500.0,
                "driver_bata_amount": 500.0,
                "total_amount": 500.0,
                "description": "Driver daily food and allowance bata",
                "expense_date": now - timedelta(days=3),
            },
            {
                "trip_id": created_trips[1].id,
                "booking_id": created_bookings[1].id,
                "vehicle_id": vehicles_map["AP09EF3456"].id,
                "category": ExpenseCategoryEnum.FUEL,
                "amount": 5800.0,
                "fuel_amount": 5800.0,
                "total_amount": 5800.0,
                "description": "Diesel 62 Litres at IndianOil NH44 Highway",
                "expense_date": now - timedelta(days=2),
            },
            {
                "trip_id": created_trips[1].id,
                "booking_id": created_bookings[1].id,
                "vehicle_id": vehicles_map["AP09EF3456"].id,
                "category": ExpenseCategoryEnum.TOLL,
                "amount": 920.0,
                "toll_amount": 920.0,
                "total_amount": 920.0,
                "description": "NH44 Toll Plaza FASTag deduction",
                "expense_date": now - timedelta(days=2),
            },
            {
                "trip_id": None,
                "booking_id": None,
                "vehicle_id": vehicles_map["TS08CD9012"].id,
                "category": ExpenseCategoryEnum.MAINTENANCE,
                "amount": 3500.0,
                "total_amount": 3500.0,
                "description": "Brake shoe replacement and wheel balance at Force Service Center",
                "expense_date": now - timedelta(days=5),
            },
        ]

        for edata in expenses_data:
            existing_e = db.query(Expense).filter(
                Expense.organization_id == org_id,
                Expense.vehicle_id == edata["vehicle_id"],
                Expense.description == edata["description"],
            ).first()
            if not existing_e:
                existing_e = Expense(organization_id=org_id, **edata)
                db.add(existing_e)
                db.flush()
                print(f"Created expense: {existing_e.description} (₹{existing_e.amount})")

        # 12. GST Invoices
        invoices_data = [
            {
                "customer_id": customers_map["Hyderabad Agro Distributors"].id,
                "trip_id": created_trips[0].id,
                "booking_id": created_bookings[0].id,
                "invoice_number": "INV-2026-001",
                "invoice_date": (now - timedelta(days=2)).date(),
                "due_date": (now + timedelta(days=12)).date(),
                "subtotal": 14500.0,
                "tax_amount": 1740.0,  # 12% GST
                "total_amount": 16240.0,
                "advance_received": 3000.0,
                "status": "paid",
                "notes": "GST @ 12% (CGST 6% + SGST 6%). Payment received via NEFT.",
            },
            {
                "customer_id": customers_map["Deccan Cement & Logistics"].id,
                "trip_id": created_trips[1].id,
                "booking_id": created_bookings[1].id,
                "invoice_number": "INV-2026-002",
                "invoice_date": (now - timedelta(days=1)).date(),
                "due_date": (now + timedelta(days=14)).date(),
                "subtotal": 18000.0,
                "tax_amount": 2160.0,  # 12% IGST
                "total_amount": 20160.0,
                "advance_received": 5000.0,
                "status": "sent",
                "notes": "GST @ 12% IGST. Payment due in 15 days.",
            },
            {
                "customer_id": customers_map["Telangana Pharma Transport"].id,
                "trip_id": created_trips[2].id,
                "booking_id": created_bookings[2].id,
                "invoice_number": "INV-2026-003",
                "invoice_date": now.date(),
                "due_date": (now + timedelta(days=15)).date(),
                "subtotal": 26500.0,
                "tax_amount": 3180.0,
                "total_amount": 29680.0,
                "advance_received": 6000.0,
                "status": "draft",
                "notes": "GST @ 12% (CGST 6% + SGST 6%). Draft awaiting trip completion.",
            },
        ]

        for idata in invoices_data:
            existing_inv = db.query(Invoice).filter(
                Invoice.organization_id == org_id,
                Invoice.invoice_number == idata["invoice_number"],
            ).first()
            if not existing_inv:
                existing_inv = Invoice(organization_id=org_id, **idata)
                db.add(existing_inv)
                db.flush()
                print(f"Created GST invoice: {existing_inv.invoice_number} (₹{existing_inv.total_amount})")
            else:
                for k, v in idata.items():
                    setattr(existing_inv, k, v)
                db.flush()

        # 13. Trip Profit Summaries
        profit_summaries = [
            {
                "trip_id": created_trips[0].id,
                "vehicle_id": vehicles_map["TS09AB1234"].id,
                "trip_revenue": 14500.0,
                "total_expense": 5450.0,
                "trip_profit": 9050.0,
                "profit_date": (now - timedelta(days=2)).date(),
                "year": now.year,
                "month": now.month,
            },
            {
                "trip_id": created_trips[1].id,
                "vehicle_id": vehicles_map["AP09EF3456"].id,
                "trip_revenue": 18000.0,
                "total_expense": 6720.0,
                "trip_profit": 11280.0,
                "profit_date": (now - timedelta(days=1)).date(),
                "year": now.year,
                "month": now.month,
            },
        ]

        for pdata in profit_summaries:
            existing_ps = db.query(TripProfitSummary).filter(
                TripProfitSummary.organization_id == org_id,
                TripProfitSummary.trip_id == pdata["trip_id"],
            ).first()
            if not existing_ps:
                existing_ps = TripProfitSummary(organization_id=org_id, **pdata)
                db.add(existing_ps)
                db.flush()
                print(f"Created profit summary for Trip {existing_ps.trip_id}: Profit ₹{existing_ps.trip_profit}")
            else:
                for k, v in pdata.items():
                    setattr(existing_ps, k, v)
                db.flush()

        # 14. Reminders
        rules_res = db.execute(text("SELECT id, name FROM reminder_rules WHERE organization_id = :oid"), {"oid": org_id}).fetchall()
        rule_map = {r[1]: r[0] for r in rules_res}
        default_rule_id = rules_res[0][0] if rules_res else 1
        ins_rule_id = rule_map.get("Insurance Expiry", default_rule_id)
        prm_rule_id = rule_map.get("Permit Expiry", default_rule_id)
        fc_rule_id = rule_map.get("FC Expiry", default_rule_id)

        reminders_data = [
            {
                "rule_id": ins_rule_id,
                "entity_type": "vehicle",
                "entity_id": vehicles_map["TS09AB1234"].id,
                "message": "Insurance for TS09AB1234 expires in 25 days. Renew with ICICI Lombard.",
                "status": "pending",
                "reminder_date": now - timedelta(days=1),
                "due_date": now + timedelta(days=25),
            },
            {
                "rule_id": prm_rule_id,
                "entity_type": "vehicle",
                "entity_id": vehicles_map["TS07UA5678"].id,
                "message": "Commercial permit for TS07UA5678 expires in 14 days at RTA Office.",
                "status": "pending",
                "reminder_date": now - timedelta(days=2),
                "due_date": now + timedelta(days=14),
            },
            {
                "rule_id": fc_rule_id,
                "entity_type": "vehicle",
                "entity_id": vehicles_map["TS08CD9012"].id,
                "message": "Fitness Certificate (FC) for TS08CD9012 expires in 15 days.",
                "status": "pending",
                "reminder_date": now - timedelta(days=3),
                "due_date": now + timedelta(days=15),
            },
            {
                "rule_id": ins_rule_id,
                "entity_type": "vehicle",
                "entity_id": vehicles_map["AP09EF3456"].id,
                "message": "Insurance for AP09EF3456 expires in 8 days. Renew immediately.",
                "status": "pending",
                "reminder_date": now,
                "due_date": now + timedelta(days=8),
            },
        ]

        for rdata in reminders_data:
            db.execute(
                text(
                    "INSERT INTO reminders (organization_id, rule_id, entity_type, entity_id, message, status, reminder_date, due_date, created_at, updated_at) "
                    "VALUES (:oid, :rule_id, :entity_type, :entity_id, :message, :status, :reminder_date, :due_date, now(), now())"
                ),
                {
                    "oid": org_id,
                    "rule_id": rdata["rule_id"],
                    "entity_type": rdata["entity_type"],
                    "entity_id": rdata["entity_id"],
                    "message": rdata["message"],
                    "status": rdata["status"],
                    "reminder_date": rdata["reminder_date"],
                    "due_date": rdata["due_date"],
                },
            )

        db.commit()
        print("Demo data seeded successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
