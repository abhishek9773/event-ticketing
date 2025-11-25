from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, List
from decimal import Decimal



class CoreSchema(BaseModel):
    """Base class to enable ORM mode for all schemas."""
    class Config:
        from_attributes = True  # Enables ORM mode for SQLAlchemy models


# ----------------- 2. User Schemas -----------------

class UserBase(BaseModel):
    username: str = Field(..., max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    """Schema for user registration and creating the initial admin."""
    password: str = Field(..., min_length=6)

class User(UserBase, CoreSchema):
    """Schema for returning user data."""
    id: int
    role: str


class Token(BaseModel):
    """Schema for JWT response upon successful login."""
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
    """Schema for creating an event (includes tags)."""
    tags: List[str] = []

class Event(EventBase, CoreSchema):
    """Schema for returning Event data to the client."""
    id: int
    organizer_id: int
    available_tickets: int
    is_active: bool
    created_at: datetime
    tags: Optional[List[str]] = []


# ----------------- 4. Ticket Schemas -----------------

class Ticket(CoreSchema):
    """Schema for returning a booked ticket to the client."""
    id: int
    event_id: int
    owner_id: int
    booking_date: datetime
    status: str
    
    # Optional nested structures
    event: Optional[Event] = None
    owner: Optional[User] = None


# ----------------- 5. Tag Schemas -----------------

class Tag(CoreSchema):
    """Schema for event tags/categories."""
    id: int
    name: str
    events: Optional[List[Event]] = []


# ----------------- 6. Analytics Schemas -----------------

class Attendee(CoreSchema):
    """Schema for attendee details in analytics report."""
    user_name: str
    user_email: str
    tickets_purchased: int

class EventAnalyticsReport(CoreSchema):
    """Schema for event analytics dashboard."""
    name: str
    date: datetime
    location: str
    description: Optional[str] = None
    
    total_tickets_sold: int
    total_revenue: float
    tickets_remaining: int
    overall_capacity: int
    
    attendees: List[Attendee]
