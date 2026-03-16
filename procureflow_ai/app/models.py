from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .db import Base


class Supplier(Base):
    __tablename__ = 'suppliers'

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    category = Column(String(80), nullable=False)
    lead_time_days = Column(Integer, nullable=False)
    on_time_rate = Column(Float, nullable=False)
    quality_score = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False)
    certifications = Column(String(220), nullable=False)
    preferred = Column(Integer, default=0, nullable=False)
    quotes = relationship('Quote', back_populates='supplier')


class Requisition(Base):
    __tablename__ = 'requisitions'

    id = Column(Integer, primary_key=True)
    title = Column(String(160), nullable=False)
    category = Column(String(80), nullable=False)
    quantity = Column(Integer, nullable=False)
    needed_by = Column(Date, nullable=False)
    priority = Column(String(30), nullable=False)
    required_certifications = Column(String(220), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    quotes = relationship('Quote', back_populates='requisition', cascade='all, delete-orphan')


class Quote(Base):
    __tablename__ = 'quotes'

    id = Column(Integer, primary_key=True)
    requisition_id = Column(Integer, ForeignKey('requisitions.id'), nullable=False)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    unit_price = Column(Float, nullable=False)
    available_qty = Column(Integer, nullable=False)
    lead_time_days = Column(Integer, nullable=False)
    note = Column(String(220), nullable=False)
    requisition = relationship('Requisition', back_populates='quotes')
    supplier = relationship('Supplier', back_populates='quotes')


class DemandSignal(Base):
    __tablename__ = 'demand_signals'

    id = Column(Integer, primary_key=True)
    category = Column(String(80), nullable=False)
    week_index = Column(Integer, nullable=False)
    units = Column(Integer, nullable=False)
