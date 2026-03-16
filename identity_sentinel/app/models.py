from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import func

from .db import Base


class SignalEvent(Base):
    __tablename__ = 'signal_events'

    id = Column(Integer, primary_key=True)
    channel = Column(String(40), nullable=False)
    sender = Column(String(120), nullable=False)
    content = Column(Text, nullable=False)
    country = Column(String(40), nullable=False)
    hour = Column(Integer, nullable=False)
    amount = Column(Float, default=0.0, nullable=False)
    new_device = Column(Boolean, default=False, nullable=False)
    new_ip = Column(Boolean, default=False, nullable=False)
    ai_voice_flag = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Alert(Base):
    __tablename__ = 'alerts'

    id = Column(Integer, primary_key=True)
    signal_id = Column(Integer, nullable=False)
    severity = Column(String(20), nullable=False)
    score = Column(Float, nullable=False)
    summary = Column(String(220), nullable=False)
    reasons = Column(Text, nullable=False)
    action = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
