from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base 

class User(Base):
    """Represents the 'users' table (Authentication & RBAC)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False) 
    hashed_password = Column(String, nullable=False)
    # The crucial Role-Based Access column
    role = Column(String, default="user", nullable=False)  # 'user' or 'admin'
    
    # Relationship to tickets
    tickets = relationship("Ticket", back_populates="owner")
    
    
class Event(Base):
    """Represents the 'events' table (Admin CRUD entity)."""
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String)
    date = Column(DateTime, nullable=False)
    location = Column(String, nullable=False)
    total_tickets = Column(Integer, nullable=False)
    # Dynamic field for booking integrity
    available_tickets = Column(Integer, nullable=False) 
    price = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relationship to tickets
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