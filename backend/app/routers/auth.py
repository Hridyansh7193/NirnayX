from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.schemas import UserCreate, UserResponse, UserLogin, TokenResponse
from app.utils.auth import hash_password, verify_password, create_access_token
from typing import Optional
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


async def seed_demo_user(db: AsyncSession):
    """Seed a demo administrator account if none exists."""
    demo_email = "demo@nirnayx.com"
    result = await db.execute(select(User).filter(User.email == demo_email))
    if not result.scalar_one_or_none():
        demo_user = User(
            email=demo_email,
            full_name="Demo Administrator",
            hashed_password=hash_password("demo1234"),
            role="admin",
            organization="NirnayX Corp",
            is_active=1
        )
        db.add(demo_user)
        await db.commit()


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    # Check for duplicate email
    result = await db.execute(select(User).filter(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password),
        role=user_data.role,
        organization=user_data.organization,
        is_active=1
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    token = create_access_token({
        "sub": str(new_user.id),
        "email": new_user.email,
        "role": new_user.role,
    })

    return TokenResponse(
        access_token=token,
        user=new_user
    )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate and receive an access token."""
    result = await db.execute(select(User).filter(User.email == credentials.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    user.last_login = datetime.utcnow()
    await db.commit()

    token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
    })

    return TokenResponse(
        access_token=token,
        user=user
    )


@router.get("/me", response_model=UserResponse)
async def get_me(db: AsyncSession = Depends(get_db)):
    """Get the profile of the demo administrator for testing."""
    result = await db.execute(select(User).filter(User.email == "demo@nirnayx.com"))
    user = result.scalar_one_or_none()
    
    if not user:
        # Seed and retry
        await seed_demo_user(db)
        result = await db.execute(select(User).filter(User.email == "demo@nirnayx.com"))
        user = result.scalar_one_or_none()
        
    if user:
        return user
    raise HTTPException(status_code=404, detail="User not found")

