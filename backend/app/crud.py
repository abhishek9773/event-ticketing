from sqlalchemy.orm import Session
from sqlalchemy import select
from app import models, schemas
from app.auth import hash_password, verify_password 
from fastapi import HTTPException, status
from typing import Optional, List


# --- User/Auth CRUD ---

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """Fetches a user by their unique username."""
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate, is_admin: bool = False) -> models.User:
    """Creates a new user (handles both standard and initial admin creation)."""
    
    # Input Validation Check 1 (prevent duplicate users)
    if get_user_by_username(db, username=user.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered"
        )
        
    hashed_pass = hash_password(user.password)
    db_user = models.User(
        username=user.username,
        email = user.email,
        hashed_password=hashed_pass,
        role="admin" if is_admin else "user"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    """Authenticates a user for login."""
    user = get_user_by_username(db, username=username)
    if not user:
        return False
    # Input Validation Check 2 (verify password)
    if not verify_password(password, user.hashed_password):
        return False
    return user


# --- Admin Event CRUD ---

def get_event_by_id(db: Session, event_id: int) -> models.Event:
    """Fetches a single event by ID, raising 404 if not found."""
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    return event

def admin_create_event(db: Session, event: schemas.EventCreate) -> models.Event:
    """Admin: Creates a new event."""
    db_event = models.Event(
        name=event.name,
        description=event.description,
        date=event.date,
        location=event.location,
        total_tickets=event.total_tickets,
        available_tickets=event.total_tickets, # Initial available tickets equals total
        price=event.price
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

def admin_update_event(db: Session, event_id: int, event_update: schemas.EventBase) -> models.Event:
    """Admin: Updates an existing event."""
    db_event = get_event_by_id(db, event_id)
    
 
    if event_update.total_tickets != db_event.total_tickets:
        diff = event_update.total_tickets - db_event.total_tickets
        db_event.available_tickets += diff
        # NOTE: More robust logic would ensure available_tickets >= 0
    
    # Update fields dynamically using Pydantic's model_dump
    update_data = event_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_event, key, value)
        
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

def admin_delete_event(db: Session, event_id: int) -> dict:
    """Admin: Deletes an event (soft delete by setting is_active=False)."""
    db_event = get_event_by_id(db, event_id)
    # Industry best practice is soft deletion
    db_event.is_active = False 
    db.commit()
    return {"detail": f"Event {event_id} successfully deactivated."}

# --- User Ticket CRUD ---

def get_all_active_events(db: Session, skip: int = 0, limit: int = 100) -> List[models.Event]:
    """Public: Fetches all active events for browsing."""
    return db.query(models.Event).filter(models.Event.is_active == True).offset(skip).limit(limit).all()

def user_book_ticket(db: Session, event_id: int, owner_id: int) -> models.Ticket:
    """
    User: Books a ticket, ensuring atomicity and availability.
    """
    db_event = get_event_by_id(db, event_id)

    # 1. Check Availability
    if db_event.available_tickets <= 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This event is sold out."
        )

    # 2. Critical: Decrement available tickets and create ticket in one transaction
    db_event.available_tickets -= 1
    
    db_ticket = models.Ticket(
        event_id=event_id,
        owner_id=owner_id,
        status="booked"
    )

    db.add(db_event) # Modify event
    db.add(db_ticket) # Create ticket
    
    # Commit both changes simultaneously to ensure integrity
    db.commit() 
    db.refresh(db_ticket)
    return db_ticket

def get_user_tickets(db: Session, owner_id: int) -> List[models.Ticket]:
    """
    User: Fetches all tickets owned by a specific user.
    """
    # Uses .options(joinedload(models.Ticket.event)) for efficient fetching (optional optimization)
    tickets = (
        db.query(models.Ticket)
        .filter(models.Ticket.owner_id == owner_id)
        .all()
    )
    return tickets