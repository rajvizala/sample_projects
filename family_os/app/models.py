from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .db import Base


class Person(Base):
    __tablename__ = 'people'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    role = Column(String(80), nullable=False)
    love_language = Column(String(80), nullable=False)
    focus = Column(String(120), nullable=False)
    updates = relationship('Update', back_populates='person', cascade='all, delete-orphan')


class Update(Base):
    __tablename__ = 'updates'

    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey('people.id'), nullable=False)
    category = Column(String(50), nullable=False)
    text = Column(Text, nullable=False)
    mood = Column(String(30), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    person = relationship('Person', back_populates='updates')


class Memory(Base):
    __tablename__ = 'memories'

    id = Column(Integer, primary_key=True)
    title = Column(String(150), nullable=False)
    detail = Column(Text, nullable=False)
    people = Column(String(200), nullable=False)
    importance = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
