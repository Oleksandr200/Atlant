from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, TypeVar
from uuid import UUID, uuid4

from fastapi import HTTPException
from pydantic import BaseModel, EmailStr

from .models import Company, Contact, Deal, TimestampedModel


class CRMStore:
    """Small in-memory store used until a persistent repository is added."""

    def __init__(self) -> None:
        self.companies: dict[UUID, Company] = {}
        self.contacts: dict[UUID, Contact] = {}
        self.deals: dict[UUID, Deal] = {}


store = CRMStore()
EntityT = TypeVar("EntityT", bound=TimestampedModel)


def now() -> datetime:
    return datetime.now(timezone.utc)


def make_entity(model: type[EntityT], payload: BaseModel) -> EntityT:
    timestamp = now()
    return model(id=uuid4(), created_at=timestamp, updated_at=timestamp, **payload.model_dump())


def get_or_404(collection: dict[UUID, Any], entity_id: UUID, entity_name: str) -> Any:
    entity = collection.get(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"{entity_name} not found")
    return entity


def require_company(company_id: UUID | None) -> None:
    if company_id is not None and company_id not in store.companies:
        raise HTTPException(status_code=400, detail="company_id does not reference a company")


def require_contact(contact_id: UUID | None) -> None:
    if contact_id is not None and contact_id not in store.contacts:
        raise HTTPException(status_code=400, detail="contact_id does not reference a contact")


def validate_unique_email(email: EmailStr, current_id: UUID | None = None) -> None:
    normalized = str(email).lower()
    if any(
        str(contact.email).lower() == normalized and contact.id != current_id
        for contact in store.contacts.values()
    ):
        raise HTTPException(status_code=409, detail="A contact with this email already exists")


def page(items: list[Any], offset: int, limit: int) -> list[Any]:
    return items[offset : offset + limit]
