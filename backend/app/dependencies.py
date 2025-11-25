from fastapi import Depends, HTTPException, status
from typing import Dict
from app.auth import oauth2_scheme, decode_access_token

def get_current_user_details(token: str = Depends(oauth2_scheme)) -> Dict[str, str]:
    """
    Decodes the JWT token provided in the Authorization header and extracts user/role.
    """
    # decode_access_token is imported from app.auth
    payload = decode_access_token(token)
    
    username: str = payload.get("sub")
    role: str = payload.get("role")
    
    if username is None or role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload (missing username or role)",
        )
    return {"username": username, "role": role}

#  Ensures the user is logged in (used for booking/viewing tickets)
def user_required(current_user: Dict = Depends(get_current_user_details)):
    """Ensures the user is authenticated (applies to 'user' and 'admin')."""
    return current_user

# Enforces Admin Role (used for Event CRUD)
def admin_required(current_user: Dict = Depends(get_current_user_details)):
    """
    Checks if the authenticated user has the 'admin' role.
    Raises: HTTPException 403 Forbidden if not admin.
    """
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied. Admin access required.",
        )
    return current_user