from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import verify_token
from app.models.user import User
from app.redis_client import redis_client

# HTTP Bearer token scheme
security = HTTPBearer()


def get_current_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Extract and verify JWT token from request."""
    token = credentials.credentials
    user_id = verify_token(token, "access")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


async def get_current_user(
    user_id: str = Depends(get_current_user_token),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current verified user."""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified"
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """Optional authentication - returns None if no token provided."""
    if credentials is None:
        return None
    
    token = credentials.credentials
    user_id = verify_token(token, "access")
    return user_id


async def rate_limit_check(
    user_id: str = Depends(get_current_user_token),
    endpoint: str = None
) -> bool:
    """Check rate limit for user."""
    if endpoint is None:
        return True
    
    # Check rate limit using Redis
    is_allowed = await redis_client.rate_limit_check(
        user_id=user_id,
        endpoint=endpoint,
        limit=100,  # 100 requests per minute
        window=60
    )
    
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    return True


class PermissionChecker:
    """Permission checker for role-based access control."""
    
    def __init__(self, required_permissions: list[str]):
        self.required_permissions = required_permissions
    
    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        """Check if user has required permissions."""
        # Superusers have all permissions
        if current_user.is_superuser:
            return current_user
        
        # Check user permissions (this would typically come from a user_permissions table)
        user_permissions = getattr(current_user, 'permissions', [])
        
        for permission in self.required_permissions:
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required"
                )
        
        return current_user


def require_permissions(*permissions: str):
    """Decorator to require specific permissions."""
    return PermissionChecker(list(permissions))


# Common permission dependencies
require_admin = require_permissions("admin")
require_read = require_permissions("read")
require_write = require_permissions("write")
require_delete = require_permissions("delete")


async def get_pagination_params(
    page: int = 1,
    limit: int = 20,
    max_limit: int = 100
) -> dict:
    """Get pagination parameters."""
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be >= 1"
        )
    
    if limit < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be >= 1"
        )
    
    if limit > max_limit:
        limit = max_limit
    
    offset = (page - 1) * limit
    
    return {"offset": offset, "limit": limit, "page": page}


async def validate_user_session(
    user_id: str = Depends(get_current_user_token)
) -> bool:
    """Validate user session."""
    session_valid = await redis_client.get_session(user_id)
    if not session_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid"
        )
    return True
