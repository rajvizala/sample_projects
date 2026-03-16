from datetime import date

from pydantic import BaseModel, Field


class RequisitionCreate(BaseModel):
    title: str = Field(min_length=4, max_length=160)
    category: str = Field(min_length=2, max_length=80)
    quantity: int = Field(ge=1)
    needed_by: date
    priority: str = Field(min_length=3, max_length=30)
    required_certifications: list[str] = []


class QuoteCreate(BaseModel):
    requisition_id: int
    supplier_id: int
    unit_price: float = Field(gt=0)
    available_qty: int = Field(ge=1)
    lead_time_days: int = Field(ge=1)
    note: str = Field(min_length=3, max_length=220)
