from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class TenantMixin:
    organization_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)


class SoftDeleteMixin:
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class Organization(Base, TimestampMixin):
    __tablename__ = 'organizations'

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default='true', nullable=False)

    users: Mapped[List['User']] = relationship('User', back_populates='organization', cascade='save-update, merge')


class Role(Base, TimestampMixin, TenantMixin):
    __tablename__ = 'roles'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    users: Mapped[List['User']] = relationship('User', secondary='user_roles', back_populates='roles')
    permissions: Mapped[List['Permission']] = relationship('Permission', secondary='role_permissions', back_populates='roles')

    __table_args__ = (
        UniqueConstraint('organization_id', 'name', name='uq_role_org_name'),
    )


class Permission(Base, TimestampMixin):
    __tablename__ = 'permissions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    resource: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    action: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    roles: Mapped[List['Role']] = relationship('Role', secondary='role_permissions', back_populates='permissions')


class RolePermission(Base):
    __tablename__ = 'role_permissions'

    role_id: Mapped[int] = mapped_column(ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
    permission_id: Mapped[int] = mapped_column(ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True)


class User(Base, TimestampMixin):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True, index=True)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default='true', nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, server_default='false', nullable=False)
    refresh_token_version: Mapped[int] = mapped_column(Integer, server_default='0', nullable=False)

    organization: Mapped[Optional[Organization]] = relationship('Organization', back_populates='users')
    roles: Mapped[List['Role']] = relationship('Role', secondary='user_roles', back_populates='users')

    __table_args__ = (
        UniqueConstraint('organization_id', 'email', name='uq_user_org_email'),
    )


class UserRole(Base):
    __tablename__ = 'user_roles'

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)


class Customer(Base, TimestampMixin, TenantMixin, SoftDeleteMixin):
    __tablename__ = 'customers'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    gst_number: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pincode: Mapped[Optional[str]] = mapped_column(String(12), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default='true', nullable=False)

    bookings: Mapped[List['Booking']] = relationship('Booking', back_populates='customer')
    invoices: Mapped[List['Invoice']] = relationship('Invoice', back_populates='customer', cascade='all, delete-orphan')

    __table_args__ = (
        UniqueConstraint('organization_id', 'phone_number', name='uq_customer_org_phone'),
        UniqueConstraint('organization_id', 'gst_number', name='uq_customer_org_gst'),
        Index('ix_customers_org_phone', 'organization_id', 'phone_number'),
        Index('ix_customers_org_gst', 'organization_id', 'gst_number'),
    )


class Vehicle(Base, TimestampMixin, TenantMixin, SoftDeleteMixin):
    __tablename__ = 'vehicles'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    vehicle_number: Mapped[str] = mapped_column(String(64), nullable=False)
    vehicle_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    make: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    seating_capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fuel_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    registration_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    insurance_expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    permit_expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    fc_expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    pollution_expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    road_tax_expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    gps_subscription_expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    service_due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    tyre_change_due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    battery_change_due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    loan_closure_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    purchase_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    emi_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    emi_due_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default='true', nullable=False)

    bookings: Mapped[List['Booking']] = relationship('Booking', back_populates='vehicle')
    calendar_events: Mapped[List['VehicleCalendarEvent']] = relationship('VehicleCalendarEvent', back_populates='vehicle', cascade='all, delete-orphan')

    __table_args__ = (
        UniqueConstraint('organization_id', 'vehicle_number', name='uq_vehicle_org_number'),
        Index('ix_vehicles_org_number', 'organization_id', 'vehicle_number'),
    )


class Driver(Base, TimestampMixin, TenantMixin, SoftDeleteMixin):
    __tablename__ = 'drivers'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    license_number: Mapped[str] = mapped_column(String(64), nullable=False)
    license_expiry: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    contact_number: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    bookings: Mapped[List['Booking']] = relationship('Booking', back_populates='driver')

    __table_args__ = (
        UniqueConstraint('organization_id', 'license_number', name='uq_driver_org_license'),
    )


class MaintenanceStatusEnum(str, enum.Enum):
    SCHEDULED = 'scheduled'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'


class CalendarEventTypeEnum(str, enum.Enum):
    BOOKING = 'booking'
    MAINTENANCE = 'maintenance'
    DISPATCH = 'dispatch'


class CalendarEventStatusEnum(str, enum.Enum):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'


class MaintenanceSchedule(Base, TimestampMixin, TenantMixin):
    __tablename__ = 'maintenance_schedule'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey('vehicles.id', ondelete='RESTRICT'), nullable=False, index=True)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=MaintenanceStatusEnum.SCHEDULED)

    vehicle: Mapped[Vehicle] = relationship('Vehicle')
    calendar_event: Mapped[Optional['VehicleCalendarEvent']] = relationship('VehicleCalendarEvent', back_populates='maintenance', uselist=False)

    __table_args__ = (
        Index('ix_maintenance_schedule_org_vehicle', 'organization_id', 'vehicle_id'),
        Index('ix_maintenance_schedule_org_start_date', 'organization_id', 'start_date'),
    )


class VehicleCalendarEvent(Base, TimestampMixin, TenantMixin):
    __tablename__ = 'vehicle_calendar_events'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey('vehicles.id', ondelete='RESTRICT'), nullable=False, index=True)
    booking_id: Mapped[Optional[int]] = mapped_column(ForeignKey('bookings.id', ondelete='CASCADE'), nullable=True, index=True)
    maintenance_id: Mapped[Optional[int]] = mapped_column(ForeignKey('maintenance_schedule.id', ondelete='CASCADE'), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(
        SQLEnum(
            CalendarEventTypeEnum,
            name='calendar_event_type',
            native_enum=True,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
            validate_strings=True,
        ),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=CalendarEventStatusEnum.PENDING)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    vehicle: Mapped[Vehicle] = relationship('Vehicle', back_populates='calendar_events')
    booking: Mapped[Optional['Booking']] = relationship('Booking', back_populates='calendar_events')
    maintenance: Mapped[Optional[MaintenanceSchedule]] = relationship('MaintenanceSchedule', back_populates='calendar_event')

    __table_args__ = (
        Index('ix_vehicle_calendar_events_org_vehicle', 'organization_id', 'vehicle_id'),
        Index('ix_vehicle_calendar_events_org_start_date', 'organization_id', 'start_date'),
    )


class BookingStatusEnum(str):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'


class Booking(Base, TimestampMixin, TenantMixin):
    __tablename__ = 'bookings'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    customer_id: Mapped[Optional[int]] = mapped_column(ForeignKey('customers.id', ondelete='RESTRICT'), nullable=True, index=True)
    customer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    customer_company: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    customer_phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    customer_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    customer_gst_number: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    customer_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    customer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey('vehicles.id', ondelete='RESTRICT'), nullable=False, index=True)
    driver_id: Mapped[Optional[int]] = mapped_column(ForeignKey('drivers.id', ondelete='SET NULL'), nullable=True, index=True)
    pickup_location: Mapped[str] = mapped_column(String(500), nullable=False)
    destination: Mapped[str] = mapped_column(String(500), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    booking_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=BookingStatusEnum.PENDING)

    customer: Mapped[Optional[Customer]] = relationship('Customer', back_populates='bookings')
    vehicle: Mapped[Vehicle] = relationship('Vehicle', back_populates='bookings')
    driver: Mapped[Optional[Driver]] = relationship('Driver', back_populates='bookings')
    trips: Mapped[List['Trip']] = relationship('Trip', back_populates='booking', cascade='all, delete-orphan')
    expenses: Mapped[List['Expense']] = relationship('Expense', back_populates='booking', cascade='all, delete-orphan')
    calendar_events: Mapped[List['VehicleCalendarEvent']] = relationship('VehicleCalendarEvent', back_populates='booking', cascade='all, delete-orphan')

    __table_args__ = (
        Index('ix_bookings_org_customer', 'organization_id', 'customer_id'),
        Index('ix_bookings_org_vehicle', 'organization_id', 'vehicle_id'),
        Index('ix_bookings_org_start_date', 'organization_id', 'start_date'),
    )


class TripStatusEnum(str, enum.Enum):
    PENDING = 'pending'
    ONGOING = 'ongoing'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'


class Trip(Base, TimestampMixin, TenantMixin):
    __tablename__ = 'trips'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False, index=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey('vehicles.id', ondelete='RESTRICT'), nullable=False, index=True)
    package_id: Mapped[Optional[int]] = mapped_column(ForeignKey('trip_packages.id', ondelete='SET NULL'), nullable=True, index=True)
    package_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    trip_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    start_place: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    end_place: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    start_km: Mapped[int] = mapped_column(BigInteger, nullable=False)
    end_km: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    distance_km: Mapped[Optional[float]] = mapped_column(Numeric(12, 3), nullable=True)
    included_km: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    included_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    hours_used: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    days_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extra_km: Mapped[Optional[float]] = mapped_column(Numeric(12, 3), nullable=True)
    extra_hours: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    package_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    extra_km_rate: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    extra_hour_rate: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    minimum_km_per_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    km_rate: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    extra_km_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    extra_hour_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    driver_bata: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    night_charges: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    permit_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    state_tax_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    toll_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    parking_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    advance_received: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True, server_default='0')
    grand_total: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    trip_revenue: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    status: Mapped[str] = mapped_column(
        SQLEnum(
            TripStatusEnum,
            name='trip_status',
            native_enum=True,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
            validate_strings=True,
        ),
        nullable=False,
        server_default=TripStatusEnum.PENDING.value,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    booking: Mapped[Booking] = relationship('Booking', back_populates='trips')
    vehicle: Mapped[Vehicle] = relationship('Vehicle')
    package: Mapped[Optional['TripPackage']] = relationship('TripPackage')
    expenses: Mapped[List['Expense']] = relationship('Expense', back_populates='trip', cascade='all, delete-orphan')
    invoices: Mapped[List['Invoice']] = relationship('Invoice', back_populates='trip', cascade='all, delete-orphan')

    __table_args__ = (
        Index('ix_trips_org_booking', 'organization_id', 'booking_id'),
        Index('ix_trips_org_vehicle', 'organization_id', 'vehicle_id'),
        Index('ix_trips_org_start', 'organization_id', 'start_time'),
    )


class TripPackage(Base, TimestampMixin, TenantMixin):
    __tablename__ = 'trip_packages'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    package_category: Mapped[str] = mapped_column(String(64), nullable=False)
    included_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    included_km: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    base_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, server_default='0')
    extra_km_rate: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    extra_hour_rate: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    driver_bata_default: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    night_charge_default: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    permit_default: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    state_tax_default: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    minimum_km_per_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    km_rate: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, server_default='true', nullable=False)

    __table_args__ = (
        UniqueConstraint('organization_id', 'name', name='uq_trip_packages_org_name'),
        Index('ix_trip_packages_org_category', 'organization_id', 'package_category'),
    )


class ExpenseCategoryEnum(str, enum.Enum):
    FUEL = 'fuel'
    TOLL = 'toll'
    PARKING = 'parking'
    MAINTENANCE = 'maintenance'
    OTHER = 'other'


class ReminderRule(Base, TimestampMixin, TenantMixin):
    __tablename__ = 'reminder_rules'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, server_default='true', nullable=False)
    trigger_days_before: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    threshold_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, server_default='100', nullable=False)
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    reminders: Mapped[List['Reminder']] = relationship('Reminder', back_populates='rule', cascade='all, delete-orphan')

    __table_args__ = (
        Index('ix_reminder_rules_org_event_type', 'organization_id', 'event_type'),
    )


class Reminder(Base, TimestampMixin, TenantMixin):
    __tablename__ = 'reminders'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey('reminder_rules.id', ondelete='CASCADE'), nullable=False, index=True)
    entity_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    reminder_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default='pending')
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    rule: Mapped[ReminderRule] = relationship('ReminderRule', back_populates='reminders')
    notification_events: Mapped[List['NotificationEvent']] = relationship('NotificationEvent', back_populates='reminder', cascade='all, delete-orphan')

    __table_args__ = (
        Index('ix_reminders_org_status', 'organization_id', 'status'),
        Index('ix_reminders_org_reminder_date', 'organization_id', 'reminder_date'),
    )


class NotificationEvent(Base, TimestampMixin, TenantMixin):
    __tablename__ = 'notification_events'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    reminder_id: Mapped[Optional[int]] = mapped_column(ForeignKey('reminders.id', ondelete='CASCADE'), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    recipient_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default='pending')
    scheduled_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    reminder: Mapped[Optional['Reminder']] = relationship('Reminder', back_populates='notification_events')

    __table_args__ = (
        Index('ix_notification_events_org_scheduled', 'organization_id', 'scheduled_time'),
    )


class NotificationPreference(Base, TimestampMixin, TenantMixin):
    __tablename__ = 'notification_preferences'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, server_default='true', nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column('metadata', JSON, nullable=True)

    __table_args__ = (
        UniqueConstraint('organization_id', 'user_id', 'event_type', 'channel', name='uq_notification_pref_org_user_event_channel'),
    )


class Expense(Base, TimestampMixin, TenantMixin):
    __tablename__ = 'expenses'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    trip_id: Mapped[Optional[int]] = mapped_column(ForeignKey('trips.id', ondelete='CASCADE'), nullable=True, index=True)
    booking_id: Mapped[Optional[int]] = mapped_column(ForeignKey('bookings.id', ondelete='SET NULL'), nullable=True, index=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey('vehicles.id', ondelete='RESTRICT'), nullable=False, index=True)
    category: Mapped[str] = mapped_column(
        SQLEnum(
            ExpenseCategoryEnum,
            name='expense_category',
            native_enum=True,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
            validate_strings=True,
        ),
        nullable=False,
        index=True,
    )
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, server_default='0')
    fuel_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True, server_default='0')
    toll_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True, server_default='0')
    parking_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True, server_default='0')
    driver_bata_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True, server_default='0')
    permit_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True, server_default='0')
    state_tax_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True, server_default='0')
    food_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True, server_default='0')
    accommodation_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True, server_default='0')
    misc_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True, server_default='0')
    total_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True, server_default='0')
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expense_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    trip: Mapped[Optional[Trip]] = relationship('Trip', back_populates='expenses')
    booking: Mapped[Optional['Booking']] = relationship('Booking')
    vehicle: Mapped[Vehicle] = relationship('Vehicle')

    __table_args__ = (
        Index('ix_expenses_org_trip', 'organization_id', 'trip_id'),
        Index('ix_expenses_org_vehicle', 'organization_id', 'vehicle_id'),
    )


class TripProfitSummary(Base, TimestampMixin, TenantMixin):
    __tablename__ = 'trip_profit_summary'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey('trips.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey('vehicles.id', ondelete='RESTRICT'), nullable=False, index=True)
    trip_revenue: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    total_expense: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    trip_profit: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    profit_date: Mapped[date] = mapped_column(Date(), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    month: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    __table_args__ = (
        Index('ix_trip_profit_summary_org_trip', 'organization_id', 'trip_id'),
        Index('ix_trip_profit_summary_org_vehicle', 'organization_id', 'vehicle_id'),
    )


class VehicleDailyProfit(Base, TimestampMixin, TenantMixin):
    __tablename__ = 'vehicle_daily_profit'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey('vehicles.id', ondelete='RESTRICT'), nullable=False, index=True)
    profit_date: Mapped[date] = mapped_column(Date(), nullable=False, index=True)
    total_revenue: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    total_expense: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    total_profit: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    __table_args__ = (
        UniqueConstraint('vehicle_id', 'profit_date', name='uq_vehicle_daily_profit_date'),
        Index('ix_vehicle_daily_profit_org_vehicle', 'organization_id', 'vehicle_id'),
    )


class VehicleMonthlyProfit(Base, TimestampMixin, TenantMixin):
    __tablename__ = 'vehicle_monthly_profit'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey('vehicles.id', ondelete='RESTRICT'), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    month: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    total_revenue: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    total_expense: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    total_profit: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    __table_args__ = (
        UniqueConstraint('vehicle_id', 'year', 'month', name='uq_vehicle_monthly_profit_period'),
        Index('ix_vehicle_monthly_profit_org_vehicle', 'organization_id', 'vehicle_id'),
    )


class InvoiceStatusEnum(str):
    DRAFT = 'draft'
    SENT = 'sent'
    PAID = 'paid'
    OVERDUE = 'overdue'


class Invoice(Base, TimestampMixin, TenantMixin):
    __tablename__ = 'invoices'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    customer_id: Mapped[Optional[int]] = mapped_column(ForeignKey('customers.id', ondelete='RESTRICT'), nullable=True, index=True)
    trip_id: Mapped[Optional[int]] = mapped_column(ForeignKey('trips.id', ondelete='CASCADE'), nullable=True, unique=True, index=True)
    booking_id: Mapped[Optional[int]] = mapped_column(ForeignKey('bookings.id', ondelete='SET NULL'), nullable=True, index=True)
    invoice_number: Mapped[str] = mapped_column(String(128), nullable=False)
    invoice_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, server_default='0')
    tax_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, server_default='0')
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, server_default='0')
    advance_received: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True, server_default='0')
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=InvoiceStatusEnum.DRAFT)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column('metadata', JSON, nullable=True)

    customer: Mapped[Optional[Customer]] = relationship('Customer', back_populates='invoices')
    trip: Mapped[Optional[Trip]] = relationship('Trip', back_populates='invoices')
    booking: Mapped[Optional['Booking']] = relationship('Booking')
    payments: Mapped[List['Payment']] = relationship('Payment', back_populates='invoice', cascade='all, delete-orphan')
    invoice_items: Mapped[List['InvoiceItem']] = relationship('InvoiceItem', back_populates='invoice', cascade='all, delete-orphan')

    __table_args__ = (
        UniqueConstraint('organization_id', 'invoice_number', name='uq_invoice_org_number'),
        Index('ix_invoices_org_customer', 'organization_id', 'customer_id'),
        Index('ix_invoices_org_trip', 'organization_id', 'trip_id'),
        Index('ix_invoices_org_booking', 'organization_id', 'booking_id'),
    )


class InvoiceItem(Base, TimestampMixin, TenantMixin):
    __tablename__ = 'invoice_items'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=False, server_default='1')
    unit_price_cents: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=False)
    line_total_cents: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column('metadata', JSON, nullable=True)

    invoice: Mapped[Invoice] = relationship('Invoice', back_populates='invoice_items')

    __table_args__ = (
        Index('ix_invoice_items_org_invoice', 'organization_id', 'invoice_id'),
    )


class Payment(Base, TimestampMixin, TenantMixin):
    __tablename__ = 'payments'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False, index=True)
    amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    method: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    transaction_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    invoice: Mapped[Invoice] = relationship('Invoice', back_populates='payments')

    __table_args__ = (
        Index('ix_payments_org_invoice', 'organization_id', 'invoice_id'),
    )


class Notification(Base, TimestampMixin, TenantMixin):
    __tablename__ = 'notifications'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    recipient_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)
    channel: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    scheduled_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    __table_args__ = (
        Index('ix_notifications_org_scheduled', 'organization_id', 'scheduled_time'),
    )


class AuditLog(Base, TimestampMixin, TenantMixin):
    __tablename__ = 'audit_logs'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)
    entity_type: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    entity_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    action: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    changes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        Index('ix_audit_org_time', 'organization_id', 'created_at'),
    )
