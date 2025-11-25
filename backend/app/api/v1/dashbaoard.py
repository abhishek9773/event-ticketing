from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import schemas, crud
from app.dependencies import get_db, get_current_admin 

router = APIRouter(
    prefix="/dashboard",
    tags=["Admin Dashboard & Analytics"]
)

@router.get(
    "/events/{event_id}/analytics", 
    response_model=schemas.EventAnalyticsReport,
)
def read_event_analytics(
    event_id: int,
    db: Session = Depends(get_db),
    current_admin: crud.models.User = Depends(get_current_admin) 
):
    report_data = crud.get_event_analytics(db, event_id=event_id)
    
    if not report_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Event with ID {event_id} not found or no data available."
        )
        
    return report_data