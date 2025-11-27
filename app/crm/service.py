from typing import Optional, List

from sqlalchemy.orm import Session

from app.models.crm import GlobalCustomer, MerchantCustomer, CustomerEvent
from .schemas import (
    GlobalCustomerCreate,
    MerchantCustomerCreate,
    MerchantCustomerUpdate,
    CustomerEventCreate,
)


def get_or_create_global_customer(
    db: Session,
    payload: GlobalCustomerCreate,
) -> GlobalCustomer:
    existing = (
        db.query(GlobalCustomer)
        .filter(GlobalCustomer.global_key == payload.global_key)
        .first()
    )
    if existing:
        # Light update
        existing.email = payload.email or existing.email
        existing.phone = payload.phone or existing.phone
        existing.first_name = payload.first_name or existing.first_name
        existing.last_name = payload.last_name or existing.last_name
        existing.tags = payload.tags or existing.tags
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    obj = GlobalCustomer(
        global_key=payload.global_key,
        email=payload.email,
        phone=payload.phone,
        first_name=payload.first_name,
        last_name=payload.last_name,
        tags=payload.tags,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def create_or_update_merchant_customer(
    db: Session,
    payload: MerchantCustomerCreate,
) -> MerchantCustomer:
    # Simple matching rule for now: merchant_id + email OR phone
    query = db.query(MerchantCustomer).filter(
        MerchantCustomer.merchant_id == payload.merchant_id
    )
    if payload.email:
        query = query.filter(MerchantCustomer.email == payload.email)
    elif payload.phone:
        query = query.filter(MerchantCustomer.phone == payload.phone)

    existing = query.first()

    global_customer_id: Optional[int] = None
    if payload.global_key:
        gc = get_or_create_global_customer(
            db,
            GlobalCustomerCreate(
                global_key=payload.global_key,
                email=payload.email,
                phone=payload.phone,
                first_name=payload.first_name,
                last_name=payload.last_name,
            ),
        )
        global_customer_id = gc.id

    if existing:
        existing.email = payload.email or existing.email
        existing.phone = payload.phone or existing.phone
        existing.first_name = payload.first_name or existing.first_name
        existing.last_name = payload.last_name or existing.last_name
        existing.status = payload.status or existing.status
        existing.segment = payload.segment or existing.segment
        existing.notes = payload.notes or existing.notes
        if global_customer_id:
            existing.global_customer_id = global_customer_id
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    obj = MerchantCustomer(
        merchant_id=payload.merchant_id,
        email=payload.email,
        phone=payload.phone,
        first_name=payload.first_name,
        last_name=payload.last_name,
        status=payload.status,
        segment=payload.segment,
        notes=payload.notes,
        global_customer_id=global_customer_id,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_merchant_customer(
    db: Session,
    merchant_customer_id: int,
    payload: MerchantCustomerUpdate,
) -> Optional[MerchantCustomer]:
    obj = (
        db.query(MerchantCustomer)
        .filter(MerchantCustomer.id == merchant_customer_id)
        .first()
    )
    if not obj:
        return None

    if payload.email is not None:
        obj.email = payload.email
    if payload.phone is not None:
        obj.phone = payload.phone
    if payload.first_name is not None:
        obj.first_name = payload.first_name
    if payload.last_name is not None:
        obj.last_name = payload.last_name
    if payload.status is not None:
        obj.status = payload.status
    if payload.segment is not None:
        obj.segment = payload.segment
    if payload.notes is not None:
        obj.notes = payload.notes

    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_merchant_customers(
    db: Session,
    merchant_id: int,
    search: Optional[str] = None,
) -> List[MerchantCustomer]:
    q = db.query(MerchantCustomer).filter(MerchantCustomer.merchant_id == merchant_id)
    if search:
        like = f"%{search}%"
        q = q.filter(
            (MerchantCustomer.email.ilike(like))
            | (MerchantCustomer.phone.ilike(like))
            | (MerchantCustomer.first_name.ilike(like))
            | (MerchantCustomer.last_name.ilike(like))
        )
    return q.order_by(MerchantCustomer.created_at.desc()).all()


def record_event(
    db: Session,
    payload: CustomerEventCreate,
) -> CustomerEvent:
    obj = CustomerEvent(
        merchant_id=payload.merchant_id,
        merchant_customer_id=payload.merchant_customer_id,
        event_type=payload.event_type,
        description=payload.description,
        extra_data=payload.extra_data,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_events_for_customer(
    db: Session,
    merchant_customer_id: int,
) -> List[CustomerEvent]:
    return (
        db.query(CustomerEvent)
        .filter(CustomerEvent.merchant_customer_id == merchant_customer_id)
        .order_by(CustomerEvent.created_at.desc())
        .all()
    )
