from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response, status

from .models import Contact, ContactCreate, ContactUpdate
from .store import (
    get_or_404,
    make_entity,
    now,
    page,
    require_company,
    store,
    validate_unique_email,
)


router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("", response_model=list[Contact])
async def list_contacts(
    search: Annotated[str | None, Query(max_length=100)] = None,
    company_id: UUID | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[Contact]:
    contacts = list(store.contacts.values())
    if search:
        needle = search.casefold()
        contacts = [
            contact
            for contact in contacts
            if needle in f"{contact.first_name} {contact.last_name}".casefold()
            or needle in str(contact.email).casefold()
        ]
    if company_id is not None:
        contacts = [contact for contact in contacts if contact.company_id == company_id]
    return page(contacts, offset, limit)


@router.post("", response_model=Contact, status_code=status.HTTP_201_CREATED)
async def create_contact(payload: ContactCreate) -> Contact:
    require_company(payload.company_id)
    validate_unique_email(payload.email)
    contact = make_entity(Contact, payload)
    store.contacts[contact.id] = contact
    return contact


@router.get("/{contact_id}", response_model=Contact)
async def get_contact(contact_id: UUID) -> Contact:
    return get_or_404(store.contacts, contact_id, "Contact")


@router.patch("/{contact_id}", response_model=Contact)
async def update_contact(contact_id: UUID, payload: ContactUpdate) -> Contact:
    contact = get_or_404(store.contacts, contact_id, "Contact")
    values = payload.model_dump(exclude_unset=True)
    require_company(values.get("company_id", contact.company_id))
    if "email" in values:
        validate_unique_email(values["email"], contact_id)
    updated = contact.model_copy(update={**values, "updated_at": now()})
    store.contacts[contact_id] = updated
    return updated


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(contact_id: UUID) -> Response:
    get_or_404(store.contacts, contact_id, "Contact")
    if any(deal.contact_id == contact_id for deal in store.deals.values()):
        raise HTTPException(status_code=409, detail="Cannot delete a contact with deals")
    del store.contacts[contact_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)
