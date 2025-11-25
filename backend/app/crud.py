from sqlalchemy.orm import Session
from app import models, schemas
from app.auth import hash_password, verify_password 
from fastapi import HTTPException, status
from typing import Optional, List



def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """Fetches a user by their unique username."""
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, user: schemas.UserCreate, is_admin: bool = False) -> models.User:
    if get_user_by_username(db, username=user.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered"
        )
        
    hashed_pass = hash_password(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
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
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail="user not found "
        )
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail="password don't match"
        )
    return user


# --- Admin Event CRUD ---

def get_event_by_id(db: Session, event_id: int) -> models.Event:

    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    return event


def create_event(db: Session, event: schemas.EventCreate, organizer_id: int) -> models.Event:
    """Creates a new event with tags (creating tags if they don’t exist)."""
    tags = []
    for tag_name in event.tags:
        tag = db.query(models.Tag).filter(models.Tag.name == tag_name).first()
        if not tag:
            tag = models.Tag(name=tag_name)
            db.add(tag)
            tags.append(tag)
        else:
            tags.append(tag)

    db_event = models.Event(
        name=event.name,
        description=event.description,
        date=event.date,
        location=event.location,
        total_tickets=event.total_tickets,
        available_tickets=event.total_tickets,
        price=event.price,
        organizer_id=organizer_id,
        tags=tags
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def admin_update_event(db: Session, event_id: int, event_update: schemas.EventBase) -> models.Event:
    """Admin: Updates an existing event."""
    db_event = get_event_by_id(db, event_id)
    
    if event_update.total_tickets and event_update.total_tickets != db_event.total_tickets:
        diff = event_update.total_tickets - db_event.total_tickets
        db_event.available_tickets += diff
        if db_event.available_tickets < 0:
            db_event.available_tickets = 0
    
    update_data = event_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_event, key, value)
        
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def admin_delete_event(db: Session, event_id: int) -> dict:
    """Admin: Soft deletes an event by setting is_active=False."""
    db_event = get_event_by_id(db, event_id)
    db_event.is_active = False
    db.commit()
    return {"detail": f"Event {event_id} successfully deactivated."}


# --- User Ticket CRUD ---

def get_all_active_events(db: Session, skip: int = 0, limit: int = 100) -> List[models.Event]:
    """Public: Fetches all active events for browsing."""
    return (
        db.query(models.Event)
        .filter(models.Event.is_active == True)
        .offset(skip)
        .limit(limit)
        .all()
    )


def user_book_ticket(db: Session, event_id: int, owner_id: int) -> models.Ticket:
    """User: Books a ticket, ensuring atomicity and availability."""
    db_event = (
        db.query(models.Event)
        .filter(models.Event.id == event_id)
        .with_for_update()
        .first()
    )
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")

    if db_event.available_tickets <= 0:
        raise HTTPException(status_code=409, detail="This event is sold out.")

    db_event.available_tickets -= 1
    
    db_ticket = models.Ticket(
        event_id=event_id,
        owner_id=owner_id,
        status="booked"
    )

    try:
        db.add(db_event)
        db.add(db_ticket)
        db.commit()
        db.refresh(db_ticket)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to book ticket.")
    
    return db_ticket


def get_user_tickets(db: Session, owner_id: int) -> List[models.Ticket]:
    """User: Fetches all tickets owned by a specific user."""
    return db.query(models.Ticket).filter(models.Ticket.owner_id == owner_id).all()


# --- Event Analytics ---

def get_event_analytics(db: Session, event_id: int):
    """Generates analytics report for a given event."""
    event = get_event_by_id(db, event_id)

    tickets_data = (
        db.query(models.Ticket, models.User)
        .join(models.User, models.Ticket.owner_id == models.User.id)
        .filter(models.Ticket.event_id == event_id)
        .all()
    )

    total_tickets_sold = len(tickets_data)
    total_revenue = total_tickets_sold * float(event.price)
    tickets_remaining = event.total_tickets - total_tickets_sold
    
    attendees_map = {}
    for ticket, user in tickets_data:
        if user.id not in attendees_map:
            attendees_map[user.id] = {
                "user_name": user.username,
                "user_email": user.email,
                "tickets_purchased": 0
            }
        attendees_map[user.id]["tickets_purchased"] += 1
    
    attendees_list = list(attendees_map.values())

    return {
        "name": event.name,
        "date": event.date,
        "location": event.location,
        "description": event.description,
        "total_tickets_sold": total_tickets_sold,
        "total_revenue": total_revenue,
        "tickets_remaining": tickets_remaining,
        "overall_capacity": event.total_tickets,
        "attendees": attendees_list
    }
