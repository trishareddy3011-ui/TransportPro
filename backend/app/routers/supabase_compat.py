from __future__ import annotations

import json
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..core.security import create_access_token, create_refresh_token, validate_token, verify_password, hash_password
from ..database import get_db
from ..models import Organization, Role, User, UserRole

router = APIRouter(tags=["supabase-compat"])


def serialize_val(val: Any) -> Any:
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    if isinstance(val, uuid.UUID):
        return str(val)
    if isinstance(val, Decimal):
        return float(val)
    return val


def serialize_row(row_dict: Dict[str, Any]) -> Dict[str, Any]:
    return {k: serialize_val(v) for k, v in row_dict.items()}


# ============================================================================
# Auth v1 Endpoints (Supabase Auth Client compatibility)
# ============================================================================

class SignUpRequest(BaseModel):
    email: str
    password: str
    data: Optional[Dict[str, Any]] = None


@router.post("/auth/v1/token")
async def auth_token(
    request: Request,
    db: Session = Depends(get_db),
):
    grant_type = request.query_params.get("grant_type", "password")
    body = await request.json()

    if grant_type == "password":
        email = body.get("email")
        password = body.get("password")
        if not email or not password:
            raise HTTPException(status_code=400, detail="Missing email or password")

        user = db.query(User).filter(User.email == email).first()
        if not user or not user.hashed_password or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Invalid login credentials")

        org_id = str(user.organization_id) if user.organization_id else "00000000-0000-0000-0000-000000000001"
        roles = [r.name for r in user.roles] if user.roles else ["admin"]

        access_token = create_access_token(user_id=str(user.id), organization_id=org_id, roles=roles)
        refresh_token = create_refresh_token(user_id=str(user.id), organization_id=org_id, refresh_version=user.refresh_token_version)

        user_data = {
            "id": str(user.id),
            "aud": "authenticated",
            "role": "authenticated",
            "email": user.email,
            "email_confirmed_at": datetime.utcnow().isoformat(),
            "phone": "",
            "confirmed_at": datetime.utcnow().isoformat(),
            "last_sign_in_at": datetime.utcnow().isoformat(),
            "app_metadata": {"provider": "email", "providers": ["email"]},
            "user_metadata": {"email": user.email, "role": roles[0] if roles else "admin"},
            "created_at": user.created_at.isoformat() if user.created_at else datetime.utcnow().isoformat(),
            "updated_at": user.updated_at.isoformat() if user.updated_at else datetime.utcnow().isoformat(),
        }

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 3600,
            "refresh_token": refresh_token,
            "user": user_data,
        }

    elif grant_type == "refresh_token":
        ref_token = body.get("refresh_token")
        if not ref_token:
            raise HTTPException(status_code=400, detail="Missing refresh token")
        try:
            payload = validate_token(ref_token, expected_type="refresh")
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        org_id = str(user.organization_id) if user.organization_id else "00000000-0000-0000-0000-000000000001"
        roles = [r.name for r in user.roles] if user.roles else ["admin"]
        new_access = create_access_token(user_id=str(user.id), organization_id=org_id, roles=roles)
        new_refresh = create_refresh_token(user_id=str(user.id), organization_id=org_id, refresh_version=user.refresh_token_version)

        return {
            "access_token": new_access,
            "token_type": "bearer",
            "expires_in": 3600,
            "refresh_token": new_refresh,
            "user": {
                "id": str(user.id),
                "aud": "authenticated",
                "role": "authenticated",
                "email": user.email,
            },
        }

    raise HTTPException(status_code=400, detail="Unsupported grant type")


@router.post("/auth/v1/signup")
async def auth_signup(
    payload: SignUpRequest,
    db: Session = Depends(get_db),
):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already registered")

    default_org_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    org = db.query(Organization).filter(Organization.id == default_org_id).first()
    if not org:
        org = Organization(id=default_org_id, name="Default Fleet")
        db.add(org)
        db.flush()

    new_user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        organization_id=default_org_id,
        is_active=True,
    )
    db.add(new_user)
    db.flush()

    admin_role = db.query(Role).filter(Role.organization_id == default_org_id, Role.name == "admin").first()
    if admin_role:
        db.add(UserRole(user_id=new_user.id, role_id=admin_role.id))

    # Add profile
    full_name = (payload.data or {}).get("name") or payload.email.split("@")[0]
    db.execute(
        text("INSERT INTO user_profiles (user_id, organization_id, full_name, role) VALUES (:uid, :oid, :name, :role) ON CONFLICT (user_id) DO NOTHING"),
        {"uid": new_user.id, "oid": default_org_id, "name": full_name, "role": "admin"}
    )
    db.commit()

    access_token = create_access_token(user_id=str(new_user.id), organization_id=str(default_org_id), roles=["admin"])
    refresh_token = create_refresh_token(user_id=str(new_user.id), organization_id=str(default_org_id), refresh_version=new_user.refresh_token_version)

    user_data = {
        "id": str(new_user.id),
        "aud": "authenticated",
        "role": "authenticated",
        "email": new_user.email,
        "email_confirmed_at": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat(),
        "app_metadata": {"provider": "email"},
        "user_metadata": {"name": full_name},
    }

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 3600,
        "refresh_token": refresh_token,
        "user": user_data,
    }


@router.get("/auth/v1/user")
def auth_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = validate_token(token, expected_type="access")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": str(user.id),
        "aud": "authenticated",
        "role": "authenticated",
        "email": user.email,
        "created_at": user.created_at.isoformat() if user.created_at else datetime.utcnow().isoformat(),
    }


@router.post("/auth/v1/logout")
def auth_logout():
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ============================================================================
# PostgREST v1 Endpoints (Supabase Query Builder compatibility)
# ============================================================================

ALLOWED_TABLES = {
    "vehicles",
    "customers",
    "drivers",
    "bookings",
    "trips",
    "trip_packages",
    "expenses",
    "invoices",
    "invoice_items",
    "payments",
    "reminders",
    "reminder_rules",
    "maintenance_schedule",
    "vehicle_calendar_events",
    "trip_profit_summary",
    "vehicle_daily_profit",
    "vehicle_monthly_profit",
    "company_settings",
    "documents",
    "user_profiles",
    "organizations",
    "users",
    "roles",
}


def parse_filters(params: Dict[str, str], bind_params: Dict[str, Any]) -> List[str]:
    where_clauses = []
    idx = 0

    for key, val in params.items():
        if key in ("select", "order", "limit", "offset", "columns"):
            continue

        param_name = f"p_{idx}"
        idx += 1

        if val == "is.null":
            where_clauses.append(f'"{key}" IS NULL')
        elif val == "is.not.null":
            where_clauses.append(f'"{key}" IS NOT NULL')
        elif val.startswith("eq."):
            where_clauses.append(f'"{key}" = :{param_name}')
            bind_params[param_name] = val[3:]
        elif val.startswith("neq."):
            where_clauses.append(f'"{key}" != :{param_name}')
            bind_params[param_name] = val[4:]
        elif val.startswith("gte."):
            where_clauses.append(f'"{key}" >= :{param_name}')
            bind_params[param_name] = val[4:]
        elif val.startswith("lte."):
            where_clauses.append(f'"{key}" <= :{param_name}')
            bind_params[param_name] = val[4:]
        elif val.startswith("gt."):
            where_clauses.append(f'"{key}" > :{param_name}')
            bind_params[param_name] = val[3:]
        elif val.startswith("lt."):
            where_clauses.append(f'"{key}" < :{param_name}')
            bind_params[param_name] = val[3:]
        elif val.startswith("ilike."):
            pattern = val[6:].replace("*", "%")
            where_clauses.append(f'"{key}"::text ILIKE :{param_name}')
            bind_params[param_name] = pattern
        elif val.startswith("in.(") and val.endswith(")"):
            inner = val[4:-1]
            raw_items = [item.strip() for item in inner.split(",") if item.strip()]
            in_clauses = []
            for j, item in enumerate(raw_items):
                p_item = f"{param_name}_{j}"
                bind_params[p_item] = item
                in_clauses.append(f":{p_item}")
            if in_clauses:
                where_clauses.append(f'"{key}" IN ({", ".join(in_clauses)})')

    return where_clauses


@router.get("/rest/v1/{table_name}")
def rest_select(
    table_name: str,
    request: Request,
    db: Session = Depends(get_db),
    accept: Optional[str] = Header(None),
):
    if table_name not in ALLOWED_TABLES:
        raise HTTPException(status_code=400, detail=f"Table {table_name} not found")

    params = dict(request.query_params)
    bind_params: Dict[str, Any] = {}
    where_clauses = parse_filters(params, bind_params)

    query = f'SELECT * FROM "{table_name}"'
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    order_param = params.get("order")
    if order_param:
        order_parts = []
        for part in order_param.split(","):
            tokens = part.strip().split(".")
            col = tokens[0]
            direction = "ASC" if len(tokens) > 1 and tokens[1].lower() == "asc" else "DESC"
            nulls = ""
            if "nullsfirst" in tokens:
                nulls = " NULLS FIRST"
            elif "nullslast" in tokens:
                nulls = " NULLS LAST"
            order_parts.append(f'"{col}" {direction}{nulls}')
        if order_parts:
            query += " ORDER BY " + ", ".join(order_parts)

    limit = params.get("limit")
    if limit and limit.isdigit():
        query += f" LIMIT {int(limit)}"

    offset = params.get("offset")
    if offset and offset.isdigit():
        query += f" OFFSET {int(offset)}"

    result = db.execute(text(query), bind_params)
    rows = [serialize_row(dict(r._mapping)) for r in result]

    # Handle PostgREST single object header
    if accept and "application/vnd.pgrst.object+json" in accept:
        if not rows:
            raise HTTPException(status_code=404, detail="JSON object requested, multiple (or no) rows returned")
        return rows[0]

    return rows


@router.post("/rest/v1/{table_name}", status_code=status.HTTP_201_CREATED)
async def rest_insert(
    table_name: str,
    request: Request,
    db: Session = Depends(get_db),
    accept: Optional[str] = Header(None),
    prefer: Optional[str] = Header(None),
):
    if table_name not in ALLOWED_TABLES:
        raise HTTPException(status_code=400, detail=f"Table {table_name} not found")

    body = await request.json()
    items = body if isinstance(body, list) else [body]
    if not items:
        return []

    inserted_rows = []
    for item in items:
        # Filter None keys or empty values where appropriate
        cols = [k for k in item.keys()]
        binds = {f"val_{i}": item[k] for i, k in enumerate(cols)}
        cols_sql = ", ".join([f'"{k}"' for k in cols])
        vals_sql = ", ".join([f":val_{i}" for i in range(len(cols))])

        insert_sql = f'INSERT INTO "{table_name}" ({cols_sql}) VALUES ({vals_sql}) RETURNING *'
        res = db.execute(text(insert_sql), binds)
        inserted = res.fetchone()
        if inserted:
            inserted_rows.append(serialize_row(dict(inserted._mapping)))

    db.commit()

    if accept and "application/vnd.pgrst.object+json" in accept:
        return inserted_rows[0] if inserted_rows else {}

    return inserted_rows


@router.patch("/rest/v1/{table_name}")
async def rest_update(
    table_name: str,
    request: Request,
    db: Session = Depends(get_db),
    accept: Optional[str] = Header(None),
):
    if table_name not in ALLOWED_TABLES:
        raise HTTPException(status_code=400, detail=f"Table {table_name} not found")

    body = await request.json()
    params = dict(request.query_params)
    bind_params: Dict[str, Any] = {}
    where_clauses = parse_filters(params, bind_params)

    set_clauses = []
    for i, (k, v) in enumerate(body.items()):
        set_param = f"set_{i}"
        bind_params[set_param] = v
        set_clauses.append(f'"{k}" = :{set_param}')

    if not set_clauses:
        return []

    update_sql = f'UPDATE "{table_name}" SET {", ".join(set_clauses)}'
    if where_clauses:
        update_sql += " WHERE " + " AND ".join(where_clauses)
    update_sql += " RETURNING *"

    res = db.execute(text(update_sql), bind_params)
    db.commit()
    rows = [serialize_row(dict(r._mapping)) for r in res]

    if accept and "application/vnd.pgrst.object+json" in accept:
        if not rows:
            raise HTTPException(status_code=404, detail="No rows found to update")
        return rows[0]

    return rows


@router.delete("/rest/v1/{table_name}")
def rest_delete(
    table_name: str,
    request: Request,
    db: Session = Depends(get_db),
):
    if table_name not in ALLOWED_TABLES:
        raise HTTPException(status_code=400, detail=f"Table {table_name} not found")

    params = dict(request.query_params)
    bind_params: Dict[str, Any] = {}
    where_clauses = parse_filters(params, bind_params)

    delete_sql = f'DELETE FROM "{table_name}"'
    if where_clauses:
        delete_sql += " WHERE " + " AND ".join(where_clauses)

    db.execute(text(delete_sql), bind_params)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
