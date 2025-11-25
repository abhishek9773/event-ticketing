from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app import schemas, crud, auth

router = APIRouter(tags=["Authentication & Users"])

# NOTE: The full path will be /v1/register (due to the prefix in main.py)
@router.post("/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Endpoint for new user registration.
    Handles input validation via schemas.UserCreate and checks for duplicates via crud.
    """
    try:
        db_user = crud.create_user(db, user)
        return db_user
    except HTTPException as e:
        # Re-raise exceptions caught in crud (e.g., 409 Conflict)
        raise e
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="An unexpected error occurred during registration."
        )


# NOTE: The full path will be /v1/login/token
@router.post("/login/token", response_model=schemas.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), # FastAPI utility for form data
    db: Session = Depends(get_db)
):
    """
    Endpoint for user login. Authenticates credentials and returns a JWT token.
    """
    user = crud.authenticate_user(db, username=form_data.username, password=form_data.password)
    
    if not user:
        # Standard security response for failed authentication
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Set token expiration time
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Create the token, including the role in the payload
    access_token = auth.create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}