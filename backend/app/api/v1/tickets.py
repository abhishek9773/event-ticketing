from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import schemas, crud
from app.dependencies import user_required

# 1. Define the API Router
router = APIRouter(
    prefix="/tickets", 
    tags=["Tickets (User Actions)"]
)

@router.post("/book/{event_id}", response_model=schemas.Ticket, status_code=status.HTTP_201_CREATED)
def book_ticket(
    event_id: int,
    user_details: dict = Depends(user_required), # Requires any authenticated user
    db: Session = Depends(get_db)
):
    """
    USER: Books one ticket for a specified event. 
    Implements the critical atomic check for available tickets.
    """
    # 1. Get the owner's ID (You need to fetch the full user object to get the ID)
    # NOTE: Since we don't have the user ID in the token payload yet (only username), 
    # we need to look up the ID from the DB.
    
    # In a production setup, the JWT payload should contain the user ID (e.g., 'uid') 
    # to avoid this extra DB call. For simplicity here:
    owner = crud.get_user_by_username(db, username=user_details["username"])
    if not owner:
        # Should not happen if token is valid, but good practice to check
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    owner_id = owner.id
    
    # 2. Call the atomic booking logic
    # This function handles the sold-out check (409 Conflict) and integrity update.
    return crud.user_book_ticket(db=db, event_id=event_id, owner_id=owner_id)

@router.get("/", response_model=List[schemas.Ticket])
def list_user_tickets(
    user_details: dict = Depends(user_required), # Requires any authenticated user
    db: Session = Depends(get_db)
):
    """
    USER: Retrieves a list of all tickets owned by the current authenticated user.
    """
    # Get the owner's ID (same lookup as above)
    owner = crud.get_user_by_username(db, username=user_details["username"])
    if not owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    owner_id = owner.id
    
    # Retrieve tickets from CRUD
    return crud.get_user_tickets(db=db, owner_id=owner_id)