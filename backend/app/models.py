from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey, Table
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base 
 


event_tag_association = Table(
    'event_tag_association', 
    Base.metadata,
    Column('event_id', ForeignKey('events.id'), primary_key=True),
    Column('tag_id', ForeignKey('tags.id'), primary_key=True)
)


class User(Base):
    """Represents the 'users' table (Authentication & RBAC)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False) 
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user", nullable=False) 
    
    # Relationship to tickets
    tickets = relationship("Ticket", back_populates="owner")
    
    # NEW: Relationship back to the events this user (admin) created
    created_events = relationship("Event", back_populates="organizer")


class Event(Base):
    """Represents the 'events' table (Admin CRUD entity)."""
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Audit Field
    organizer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    name = Column(String, index=True, nullable=False)
    description = Column(String)
    date = Column(DateTime, nullable=False)
    location = Column(String, nullable=False)
    total_tickets = Column(Integer, nullable=False)
    available_tickets = Column(Integer, nullable=False) 
    price = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    organizer = relationship("User", back_populates="created_events")
    
    
    tags = relationship("Tag", secondary=event_tag_association, back_populates="events")
    tickets = relationship("Ticket", back_populates="event")


class Ticket(Base):
    """Represents the 'tickets' table (User booking entity)."""
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    # Foreign Keys
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    booking_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="booked")
    
    # Relationships
    owner = relationship("User", back_populates="tickets")
    event = relationship("Event", back_populates="tickets")


class Tag(Base):
    """Represents the 'tags' table (Event categories)."""
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    
    
    events = relationship("Event", secondary=event_tag_association, back_populates="tags")