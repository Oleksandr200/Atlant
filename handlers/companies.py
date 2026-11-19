from __future__ import annotations

from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.database import get_db
from db.db_models import CompanyDB, ContactDB, DealDB, utc_now
from .models import Company, CompanyCreate, CompanyUpdate
from .store import get_or_404, page


router = APIRouter(prefix="/companies", tags=["companies"])
DBSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[Company])
def list_companies(
    db: DBSession,
    search: Annotated[str | None, Query(max_length=100)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[CompanyDB]:
    query = select(CompanyDB).order_by(CompanyDB.created_at)
    if search:
        query = query.where(CompanyDB.name.ilike(f"%{search}%"))
    return page(list(db.scalars(query)), offset, limit)


@router.post("", response_model=Company, status_code=status.HTTP_201_CREATED)
def create_company(payload: CompanyCreate, db: DBSession) -> CompanyDB:
    company = CompanyDB(id=str(uuid4()), **payload.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("/{company_id}", response_model=Company)
def get_company(company_id: UUID, db: DBSession) -> CompanyDB:
    return get_or_404(db, CompanyDB, company_id, "Company")


@router.patch("/{company_id}", response_model=Company)
def update_company(company_id: UUID, payload: CompanyUpdate, db: DBSession) -> CompanyDB:
    company = get_or_404(db, CompanyDB, company_id, "Company")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(company, field, value)
    company.updated_at = utc_now()
    db.commit()
    db.refresh(company)
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(company_id: UUID, db: DBSession) -> Response:
    company = get_or_404(db, CompanyDB, company_id, "Company")
    if db.scalar(select(ContactDB.id).where(ContactDB.company_id == str(company_id)).limit(1)):
        raise HTTPException(status_code=409, detail="Cannot delete a company with contacts")
    if db.scalar(select(DealDB.id).where(DealDB.company_id == str(company_id)).limit(1)):
        raise HTTPException(status_code=409, detail="Cannot delete a company with deals")
    db.delete(company)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
