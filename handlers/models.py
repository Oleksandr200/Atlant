from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CRMModel(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class TimestampedModel(CRMModel):
    id: UUID
    created_at: datetime
    updated_at: datetime


class CompanyCreate(CRMModel):
    name: Annotated[str, Field(min_length=1, max_length=200)]
    website: Annotated[str | None, Field(max_length=500)] = None
    industry: Annotated[str | None, Field(max_length=100)] = None
    notes: Annotated[str | None, Field(max_length=5000)] = None


class CompanyUpdate(CRMModel):
    name: Annotated[str | None, Field(min_length=1, max_length=200)] = None
    website: Annotated[str | None, Field(max_length=500)] = None
    industry: Annotated[str | None, Field(max_length=100)] = None
    notes: Annotated[str | None, Field(max_length=5000)] = None


class Company(TimestampedModel, CompanyCreate):
    pass


class ContactCreate(CRMModel):
    first_name: Annotated[str, Field(min_length=1, max_length=100)]
    last_name: Annotated[str, Field(min_length=1, max_length=100)]
    email: EmailStr
    phone: Annotated[str | None, Field(max_length=50)] = None
    job_title: Annotated[str | None, Field(max_length=150)] = None
    company_id: UUID | None = None
    notes: Annotated[str | None, Field(max_length=5000)] = None


class ContactUpdate(CRMModel):
    first_name: Annotated[str | None, Field(min_length=1, max_length=100)] = None
    last_name: Annotated[str | None, Field(min_length=1, max_length=100)] = None
    email: EmailStr | None = None
    phone: Annotated[str | None, Field(max_length=50)] = None
    job_title: Annotated[str | None, Field(max_length=150)] = None
    company_id: UUID | None = None
    notes: Annotated[str | None, Field(max_length=5000)] = None


class Contact(TimestampedModel, ContactCreate):
    pass


class DealStage(StrEnum):
    lead = "lead"
    qualified = "qualified"
    proposal = "proposal"
    negotiation = "negotiation"
    won = "won"
    lost = "lost"


class DealCreate(CRMModel):
    name: Annotated[str, Field(min_length=1, max_length=200)]
    value: Annotated[float, Field(ge=0)] = 0
    stage: DealStage = DealStage.lead
    company_id: UUID | None = None
    contact_id: UUID | None = None
    expected_close_date: datetime | None = None
    notes: Annotated[str | None, Field(max_length=5000)] = None


class DealUpdate(CRMModel):
    name: Annotated[str | None, Field(min_length=1, max_length=200)] = None
    value: Annotated[float | None, Field(ge=0)] = None
    stage: DealStage | None = None
    company_id: UUID | None = None
    contact_id: UUID | None = None
    expected_close_date: datetime | None = None
    notes: Annotated[str | None, Field(max_length=5000)] = None


class Deal(TimestampedModel, DealCreate):
    pass
