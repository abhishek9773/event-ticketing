from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, List
from decimal import Decimal


# ----------------- 1. Base/Config Schema -----------------

class CoreSchema(BaseModel):
    """Base class to enable ORM mode for all schemas."""
    class Config:
        # Allows Pydantic to read data from SQL Alchemy models (ORM)
        # Fixes: Setting the attribute name for Pydantic v2
        from_attributes = True 

# ----------------- 2. User Schemas -----------------

class UserBase(BaseModel):
    # This acts as a base for both UserCreate and User output
    username: str = Field(..., max_length=50)

    email: EmailStr 

class UserCreate(UserBase):
    """Schema for user registration and creating the initial admin."""
    # Inherits username and email from UserBase
    password: str = Field(..., min_length=6) 
    
    
class User(UserBase, CoreSchema):
    """User schema for output responses (includes DB fields)."""
    id: int
    role: str 


class Token(BaseModel):
    """Schema for the JWT response upon successful login."""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Schema for data retrieved from the JWT payload."""
    username: Optional[str] = None
    role: Optional[str] = None

# ----------------- 3. Event Schemas -----------------

class EventBase(BaseModel):
    """Base schema for creating and updating an Event."""
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    date: datetime
    location: str = Field(..., max_length=100)
    total_tickets: int = Field(..., gt=0)
    price: Decimal = Field(..., gt=0)

class EventCreate(EventBase):
    pass 


class Event(EventBase, CoreSchema):
    """Schema for returning Event data to the client."""
    id: int
    available_tickets: int
    is_active: bool
    
# ----------------- 4. Ticket Schemas (User Booking) -----------------

class Ticket(CoreSchema):
    """Schema for returning a booked ticket to the client."""
    id: int
    event_id: int
    owner_id: int
    booking_date: datetime
    status: str
    
    # Optional nested structure to display event details with the ticket
    event: Optional[Event] = None