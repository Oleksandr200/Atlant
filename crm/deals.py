from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from .models import Deal, DealCreate, DealStage, DealUpdate
from .store import (
    get_or_404,
    make_entity,
    now,
    page,
    require_company,
    require_contact,
    store,
)


router = APIRouter(prefix="/deals", tags=["deals"])


@router.get("", response_model=list[Deal])
async def list_deals(
    stage: DealStage | None = None,
    company_id: UUID | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[Deal]:
    deals = list(store.deals.values())
    if stage is not None:
        deals = [deal for deal in deals if deal.stage == stage]
    if company_id is not None:
        deals = [deal for deal in deals if deal.company_id == company_id]
    return page(deals, offset, limit)


@router.post("", response_model=Deal, status_code=status.HTTP_201_CREATED)
async def create_deal(payload: DealCreate) -> Deal:
    require_company(payload.company_id)
    require_contact(payload.contact_id)
    deal = make_entity(Deal, payload)
    store.deals[deal.id] = deal
    return deal


@router.get("/{deal_id}", response_model=Deal)
async def get_deal(deal_id: UUID) -> Deal:
    return get_or_404(store.deals, deal_id, "Deal")


@router.patch("/{deal_id}", response_model=Deal)
async def update_deal(deal_id: UUID, payload: DealUpdate) -> Deal:
    deal = get_or_404(store.deals, deal_id, "Deal")
    values = payload.model_dump(exclude_unset=True)
    require_company(values.get("company_id", deal.company_id))
    require_contact(values.get("contact_id", deal.contact_id))
    updated = deal.model_copy(update={**values, "updated_at": now()})
    store.deals[deal_id] = updated
    return updated


@router.delete("/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deal(deal_id: UUID) -> Response:
    get_or_404(store.deals, deal_id, "Deal")
    del store.deals[deal_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)
