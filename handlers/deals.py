from __future__ import annotations

from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.database import get_db
from db.db_models import DealDB, utc_now
from .models import Deal, DealCreate, DealStage, DealUpdate
from .store import get_or_404, page, require_company, require_contact


router = APIRouter(prefix="/deals", tags=["deals"])
DBSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[Deal])
def list_deals(
    db: DBSession,
    stage: DealStage | None = None,
    company_id: UUID | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[DealDB]:
    query = select(DealDB).order_by(DealDB.created_at)
    if stage is not None:
        query = query.where(DealDB.stage == stage.value)
    if company_id is not None:
        query = query.where(DealDB.company_id == str(company_id))
    return page(list(db.scalars(query)), offset, limit)


@router.post("", response_model=Deal, status_code=status.HTTP_201_CREATED)
def create_deal(payload: DealCreate, db: DBSession) -> DealDB:
    require_company(db, payload.company_id)
    require_contact(db, payload.contact_id)
    values = payload.model_dump()
    values["company_id"] = str(payload.company_id) if payload.company_id else None
    values["contact_id"] = str(payload.contact_id) if payload.contact_id else None
    values["stage"] = payload.stage.value
    deal = DealDB(id=str(uuid4()), **values)
    db.add(deal)
    db.commit()
    db.refresh(deal)
    return deal


@router.get("/{deal_id}", response_model=Deal)
def get_deal(deal_id: UUID, db: DBSession) -> DealDB:
    return get_or_404(db, DealDB, deal_id, "Deal")


@router.patch("/{deal_id}", response_model=Deal)
def update_deal(deal_id: UUID, payload: DealUpdate, db: DBSession) -> DealDB:
    deal = get_or_404(db, DealDB, deal_id, "Deal")
    values = payload.model_dump(exclude_unset=True)
    require_company(db, values.get("company_id", UUID(deal.company_id) if deal.company_id else None))
    require_contact(db, values.get("contact_id", UUID(deal.contact_id) if deal.contact_id else None))
    if "company_id" in values:
        values["company_id"] = str(values["company_id"]) if values["company_id"] else None
    if "contact_id" in values:
        values["contact_id"] = str(values["contact_id"]) if values["contact_id"] else None
    if "stage" in values:
        values["stage"] = values["stage"].value
    for field, value in values.items():
        setattr(deal, field, value)
    deal.updated_at = utc_now()
    db.commit()
    db.refresh(deal)
    return deal


@router.delete("/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deal(deal_id: UUID, db: DBSession) -> Response:
    deal = get_or_404(db, DealDB, deal_id, "Deal")
    db.delete(deal)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
