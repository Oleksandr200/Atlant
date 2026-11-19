from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import HTTPException
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.db_models import CompanyDB, ContactDB


def get_or_404(db: Session, model: type[Any], entity_id: UUID, entity_name: str) -> Any:
    entity = db.get(model, str(entity_id))
    if entity is None:
        raise HTTPException(status_code=404, detail=f"{entity_name} not found")
    return entity


def require_company(db: Session, company_id: UUID | None) -> None:
    if company_id is not None and db.get(CompanyDB, str(company_id)) is None:
        raise HTTPException(status_code=400, detail="company_id does not reference a company")


def require_contact(db: Session, contact_id: UUID | None) -> None:
    if contact_id is not None and db.get(ContactDB, str(contact_id)) is None:
        raise HTTPException(status_code=400, detail="contact_id does not reference a contact")


def validate_unique_email(db: Session, email: EmailStr, current_id: UUID | None = None) -> None:
    query = select(ContactDB).where(ContactDB.email == str(email).lower())
    if current_id is not None:
        query = query.where(ContactDB.id != str(current_id))
    if db.scalar(query) is not None:
        raise HTTPException(status_code=409, detail="A contact with this email already exists")


def page(items: list[Any], offset: int, limit: int) -> list[Any]:
    return items[offset : offset + limit]
