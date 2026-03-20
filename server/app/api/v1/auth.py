from typing import Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import (
    UserCreate, UserResponse, UserLogin, Token, TokenRefresh,
    UserResponseWithToken, UserUpdate, UserChangePassword
)
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_user, get_current_active_user
from app.models.user import User
from app.core.security import verify_token, create_access_token, create_refresh_token
from app.redis_client import redis_client
from app.config import settings

import httpx
import secrets
import string
from urllib.parse import urlencode

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=UserResponseWithToken, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """Register a new user."""
    user = AuthService.create_user(db, user_data)
    
    # Create tokens
    access_token = AuthService.create_access_token(str(user.id))
    refresh_token = AuthService.create_refresh_token(str(user.id))
    
    # Store session
    session_data = {
        "user_id": str(user.id),
        "email": user.email,
        "username": user.username,
        "is_superuser": user.is_superuser,
        "login_time": datetime.utcnow().isoformat()
    }
    await redis_client.set_session(str(user.id), session_data)
    
    return UserResponseWithToken(
        **user.__dict__,
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=30 * 60  # 30 minutes in seconds
    )


@router.post("/login", response_model=UserResponseWithToken)
async def login(
    user_credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """Login user and return tokens."""
    login_result = await AuthService.login_user(
        db, user_credentials.email, user_credentials.password
    )
    
    return UserResponseWithToken(
        **login_result["user"].__dict__,
        access_token=login_result["access_token"],
        refresh_token=login_result["refresh_token"],
        token_type=login_result["token_type"],
        expires_in=login_result["expires_in"]
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
) -> Any:
    """Refresh access token."""
    refresh_result = await AuthService.refresh_token(token_data.refresh_token)
    
    return Token(
        access_token=refresh_result["access_token"],
        token_type=refresh_result["token_type"],
        expires_in=refresh_result["expires_in"]
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Logout user."""
    await AuthService.logout_user(str(current_user.id))
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get current user information."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update current user information."""
    updated_user = AuthService.update_user(db, str(current_user.id), user_data)
    return updated_user


@router.post("/change-password")
async def change_password(
    password_data: UserChangePassword,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Change user password."""
    AuthService.change_password(db, str(current_user.id), password_data)
    
    # Logout all sessions (force re-login with new password)
    await AuthService.logout_user(str(current_user.id))
    
    return {"message": "Password changed successfully"}


@router.post("/forgot-password")
async def forgot_password(
    email: str,
    db: Session = Depends(get_db)
) -> Any:
    """Request password reset."""
    user = AuthService.get_user_by_email(db, email)
    if not user:
        # Don't reveal if user exists or not
        return {"message": "If email exists, reset instructions have been sent"}
    
    reset_token = AuthService.create_password_reset_token(email)
    
    # In a real application, you would send this via email
    # For now, just return the token (for development)
    return {
        "message": "Password reset token generated",
        "reset_token": reset_token  # Only for development
    }


@router.post("/reset-password")
async def reset_password(
    token: str,
    new_password: str,
    db: Session = Depends(get_db)
) -> Any:
    """Reset password using token."""
    AuthService.reset_password(db, token, new_password)
    return {"message": "Password reset successfully"}


@router.post("/verify-email")
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
) -> Any:
    """Verify email using token."""
    AuthService.verify_email(db, token)
    return {"message": "Email verified successfully"}


@router.post("/resend-verification")
async def resend_verification(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Resend email verification."""
    if current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    verification_token = AuthService.create_email_verification_token(current_user.email)
    
    # In a real application, you would send this via email
    return {
        "message": "Verification email sent",
        "verification_token": verification_token  # Only for development
    }


@router.delete("/deactivate")
async def deactivate_account(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Deactivate user account."""
    AuthService.deactivate_user(db, str(current_user.id))
    await AuthService.logout_user(str(current_user.id))
    return {"message": "Account deactivated successfully"}


# --- Google OAuth ---

def _generate_state_token(length: int = 32) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


@router.get("/auth/google/login")
async def google_login() -> Any:
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_REDIRECT_URI:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")

    state = _generate_state_token()
    # store CSRF state in redis with short TTL
    await redis_client.set(f"oauth_state:{state}", "1", expire=600)

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "consent",
        "state": state,
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return RedirectResponse(url)


@router.get("/auth/google/callback")
async def google_callback(code: str = Query(...), state: str = Query(""), request: Request = None, db: Session = Depends(get_db)) -> Any:
    # validate state
    state_ok = await redis_client.get(f"oauth_state:{state}") if state else None
    if not state_ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")

    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET or not settings.GOOGLE_REDIRECT_URI:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")

    # exchange code for tokens
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        token_resp = await client.post(token_url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        if token_resp.status_code != 200:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token exchange failed")
        token_json = token_resp.json()
        access_token = token_json.get("access_token")
        if not access_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing access token")

        # fetch userinfo
        userinfo_resp = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_resp.status_code != 200:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to fetch user info")
        userinfo = userinfo_resp.json()

    email = userinfo.get("email")
    full_name = userinfo.get("name") or "Google User"
    email_verified = bool(userinfo.get("email_verified", False))
    username_candidate = (email.split("@", 1)[0] if email else full_name.replace(" ", "").lower())[:30]

    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google account has no email")

    # find or create user
    user = AuthService.get_user_by_email(db, email)
    if not user:
        # create a pseudo-random password for OAuth user
        random_pwd = _generate_state_token(48)
        user = AuthService.create_user(db, type("UserCreate", (), {
            "email": email,
            "username": username_candidate,
            "password": random_pwd,
            "full_name": full_name,
            "is_active": True,
        })())
        # mark verified if Google verifies email
        user.is_verified = email_verified
        db.commit()
        db.refresh(user)

    # issue app tokens and create session
    access = create_access_token(subject=str(user.id))
    refresh = create_refresh_token(subject=str(user.id))
    session_data = {
        "user_id": str(user.id),
        "email": user.email,
        "username": user.username,
        "is_superuser": user.is_superuser,
        "login_time": datetime.utcnow().isoformat(),
        "provider": "google",
    }
    await redis_client.set_session(str(user.id), session_data)

    # redirect to frontend with tokens in hash for the SPA to consume
    frontend = settings.FRONTEND_ORIGIN.rstrip("/")
    hash_params = urlencode({
        "access_token": access,
        "refresh_token": refresh,
        "email": user.email,
        "name": user.username or full_name,
    })
    return RedirectResponse(url=f"{frontend}/login#" + hash_params)
