from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response, status

from .models import Company, CompanyCreate, CompanyUpdate
from .store import get_or_404, make_entity, now, page, store


router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=list[Company])
async def list_companies(
    search: Annotated[str | None, Query(max_length=100)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[Company]:
    companies = list(store.companies.values())
    if search:
        needle = search.casefold()
        companies = [company for company in companies if needle in company.name.casefold()]
    return page(companies, offset, limit)


@router.post("", response_model=Company, status_code=status.HTTP_201_CREATED)
async def create_company(payload: CompanyCreate) -> Company:
    company = make_entity(Company, payload)
    store.companies[company.id] = company
    return company


@router.get("/{company_id}", response_model=Company)
async def get_company(company_id: UUID) -> Company:
    return get_or_404(store.companies, company_id, "Company")


@router.patch("/{company_id}", response_model=Company)
async def update_company(company_id: UUID, payload: CompanyUpdate) -> Company:
    company = get_or_404(store.companies, company_id, "Company")
    updated = company.model_copy(
        update={**payload.model_dump(exclude_unset=True), "updated_at": now()}
    )
    store.companies[company_id] = updated
    return updated


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(company_id: UUID) -> Response:
    get_or_404(store.companies, company_id, "Company")
    if any(contact.company_id == company_id for contact in store.contacts.values()):
        raise HTTPException(status_code=409, detail="Cannot delete a company with contacts")
    if any(deal.company_id == company_id for deal in store.deals.values()):
        raise HTTPException(status_code=409, detail="Cannot delete a company with deals")
    del store.companies[company_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)
