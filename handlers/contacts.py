from __future__ import annotations

from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.database import get_db
from db.db_models import ContactDB, DealDB, utc_now
from .models import Contact, ContactCreate, ContactUpdate
from .store import get_or_404, page, require_company, validate_unique_email


router = APIRouter(prefix="/contacts", tags=["contacts"])
DBSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[Contact])
def list_contacts(
    db: DBSession,
    search: Annotated[str | None, Query(max_length=100)] = None,
    company_id: UUID | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[ContactDB]:
    query = select(ContactDB).order_by(ContactDB.created_at)
    if search:
        needle = f"%{search}%"
        query = query.where(
            ContactDB.first_name.ilike(needle)
            | ContactDB.last_name.ilike(needle)
            | ContactDB.email.ilike(needle)
        )
    if company_id is not None:
        query = query.where(ContactDB.company_id == str(company_id))
    return page(list(db.scalars(query)), offset, limit)


@router.post("", response_model=Contact, status_code=status.HTTP_201_CREATED)
def create_contact(payload: ContactCreate, db: DBSession) -> ContactDB:
    require_company(db, payload.company_id)
    validate_unique_email(db, payload.email)
    values = payload.model_dump()
    values["company_id"] = str(payload.company_id) if payload.company_id else None
    contact = ContactDB(id=str(uuid4()), **values)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.get("/{contact_id}", response_model=Contact)
def get_contact(contact_id: UUID, db: DBSession) -> ContactDB:
    return get_or_404(db, ContactDB, contact_id, "Contact")


@router.patch("/{contact_id}", response_model=Contact)
def update_contact(contact_id: UUID, payload: ContactUpdate, db: DBSession) -> ContactDB:
    contact = get_or_404(db, ContactDB, contact_id, "Contact")
    values = payload.model_dump(exclude_unset=True)
    require_company(db, values.get("company_id", UUID(contact.company_id) if contact.company_id else None))
    if "email" in values:
        validate_unique_email(db, values["email"], contact_id)
    if "company_id" in values:
        values["company_id"] = str(values["company_id"]) if values["company_id"] else None
    for field, value in values.items():
        setattr(contact, field, value)
    contact.updated_at = utc_now()
    db.commit()
    db.refresh(contact)
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(contact_id: UUID, db: DBSession) -> Response:
    contact = get_or_404(db, ContactDB, contact_id, "Contact")
    if db.scalar(select(DealDB.id).where(DealDB.contact_id == str(contact_id)).limit(1)):
        raise HTTPException(status_code=409, detail="Cannot delete a contact with deals")
    db.delete(contact)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
