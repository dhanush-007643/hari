"""
DataVista+ Authentication API
Handles user registration, login, token management, and profile operations
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from app.core.database import get_db
from app.core.security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token,
    decode_token, validate_password_strength
)
from app.models.user_model import User, Role
from app.models.report_model import AuditLog, ActivityLog

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# --- Pydantic Schemas ---

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Optional[dict] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


# --- Dependency ---

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    payload = decode_token(token)
    user_id = int(payload.get("sub"))
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    return user


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


# --- Routes ---

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    # Validate password strength
    if not validate_password_strength(user_data.password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 chars with uppercase, lowercase, and digit"
        )

    # Check duplicates
    result = await db.execute(
        select(User).where(
            (User.email == user_data.email) | (User.username == user_data.username)
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email or username already registered")

    # Get default analyst role
    role_result = await db.execute(select(Role).where(Role.name == "analyst"))
    role = role_result.scalar_one_or_none()

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        is_active=True,
        is_superuser=False,
        role_id=role.id if role else None,
    )
    db.add(new_user)
    await db.flush()

    # Log activity
    db.add(ActivityLog(user_id=new_user.id, action_type="register", description="New user registered"))
    await db.commit()

    return {"message": "User registered successfully", "user_id": new_user.id}


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and return JWT tokens (supports both Form & JSON)."""
    username_input = None
    password_input = None

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            username_input = body.get("username") or body.get("email")
            password_input = body.get("password")
        except Exception:
            pass
    else:
        try:
            form = await request.form()
            username_input = form.get("username") or form.get("email")
            password_input = form.get("password")
        except Exception:
            pass

    if not username_input or not password_input:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username/Email and Password are required"
        )

    # Support login by email OR username
    result = await db.execute(
        select(User).where(
            (User.email == str(username_input).strip()) | (User.username == str(username_input).strip())
        )
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(str(password_input), user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    # Update last login
    await db.execute(
        update(User).where(User.id == user.id).values(last_login=datetime.utcnow())
    )

    # Create tokens
    token_data = {"sub": str(user.id), "email": user.email, "role": user.role_id}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Log activity
    client_ip = request.client.host if request and request.client else "unknown"
    db.add(ActivityLog(
        user_id=user.id, action_type="login",
        description=f"User logged in from {client_ip}"
    ))
    db.add(AuditLog(
        user_id=user.id, action="LOGIN",
        ip_address=client_ip
    ))
    await db.commit()

    role_result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = role_result.scalar_one_or_none()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "is_superuser": user.is_superuser,
            "role": role.name if role else "viewer",
            "avatar_url": user.avatar_url,
            "preferences": user.preferences or {},
        }
    )


@router.post("/refresh")
async def refresh_token(token: str, db: AsyncSession = Depends(get_db)):
    """Refresh access token using a valid refresh token."""
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=400, detail="Invalid refresh token")

    user_id = int(payload.get("sub"))
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    new_token = create_access_token({"sub": str(user.id), "email": user.email})
    return {"access_token": new_token, "token_type": "bearer"}


@router.get("/me")
async def get_profile(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get current user profile."""
    role_result = await db.execute(select(Role).where(Role.id == current_user.role_id))
    role = role_result.scalar_one_or_none()

    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "avatar_url": current_user.avatar_url,
        "is_superuser": current_user.is_superuser,
        "role": role.name if role else "viewer",
        "preferences": current_user.preferences or {},
        "last_login": current_user.last_login,
        "created_at": current_user.created_at,
    }


@router.put("/me")
async def update_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile."""
    updates = {k: v for k, v in update_data.dict().items() if v is not None}
    if updates:
        await db.execute(update(User).where(User.id == current_user.id).values(**updates))
        await db.commit()
    return {"message": "Profile updated successfully"}


@router.post("/change-password")
async def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password."""
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    if not validate_password_strength(data.new_password):
        raise HTTPException(status_code=400, detail="New password does not meet requirements")

    await db.execute(
        update(User).where(User.id == current_user.id).values(
            hashed_password=get_password_hash(data.new_password)
        )
    )
    db.add(AuditLog(user_id=current_user.id, action="PASSWORD_CHANGE"))
    await db.commit()
    return {"message": "Password changed successfully"}
