from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import schemas, crud, models
from app.dependencies import get_current_admin_user

router = APIRouter(
    prefix="/events", 
    tags=["Events (Admin/Public)"]
)

# --- 1. ADMIN-ONLY ROUTES (Protected by admin_required) ---

@router.post("/", response_model=schemas.Event, status_code=status.HTTP_201_CREATED)
def create_event(
    event: schemas.EventCreate,
    admin_user: dict = Depends(get_current_admin_user), # RBAC enforcement!
    db: Session = Depends(get_db)
):
    """
    ADMIN: Creates a new event entry.
    Requires JWT token with 'admin' role.
    """
    return crud.admin_create_event(db=db, event=event)

@router.put("/{event_id}", response_model=schemas.Event)
def update_event(
    event_id: int,
    event_update: schemas.EventBase,
    admin_user: dict = Depends(get_current_admin_user), # RBAC enforcement!
    db: Session = Depends(get_db)
):
    """
    ADMIN: Updates an existing event. Handles changes to ticket quantities.
    Requires JWT token with 'admin' role.
    """
    return crud.admin_update_event(db=db, event_id=event_id, event_update=event_update)

@router.delete("/{event_id}", status_code=status.HTTP_200_OK)
def delete_event(
    event_id: int,
    admin_user: dict = Depends(get_current_admin_user), # RBAC enforcement!
    db: Session = Depends(get_db)
):
    """
    ADMIN: Deactivates (soft-deletes) an event.
    Requires JWT token with 'admin' role.
    """
 
    return crud.admin_delete_event(db=db, event_id=event_id)




@router.get("/", response_model=List[schemas.Event])
def list_active_events(db: Session = Depends(get_db)):
    """
    PUBLIC: Lists all currently active events for browsing.
    """
    return crud.get_all_active_events(db=db)

@router.get("/{event_id}", response_model=schemas.Event)
def get_event(event_id: int, db: Session = Depends(get_db)):
    """
    PUBLIC: Retrieves details for a specific event.
    """
    # crud.get_event_by_id handles the 404 error if the event is not found.
    return crud.get_event_by_id(db, event_id)



@router.get(
    "/{event_id}/analytics", 
    response_model=schemas.EventAnalyticsReport,
    dependencies=[Depends(get_current_admin_user)] # deps is now defined
)
def read_event_analytics(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user) # models is now defined
):
    """
    (ADMIN ONLY) Retrieves sales, revenue, and attendee data for a specific event.
    """
    report_data = crud.get_event_analytics(db, event_id=event_id)
    
    if not report_data:
        raise HTTPException(status_code=404, detail="Event not found")
        
    return report_data