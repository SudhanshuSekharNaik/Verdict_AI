from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database.session import get_db
from app.models.user import User
from app.schemas.response import APIResponse
from app.schemas.user import Token, UserCreate, UserLogin, UserResponse
from app.security.dependencies import get_current_user
from app.security.jwt import create_access_token
from app.security.passwords import get_password_hash, verify_password

router = APIRouter()


@router.post("/register", response_model=APIResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_in.email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists in Aadalat AI",
        )
    
    db_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role,
        is_active=True,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return APIResponse(success=True, data=UserResponse.model_validate(db_user))


@router.post("/login", response_model=APIResponse[Token])
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalars().first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is inactive",
        )
    
    token_str = create_access_token(subject=user.id, role=user.role.value)
    token_data = Token(
        access_token=token_str,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )
    return APIResponse(success=True, data=token_data)


@router.get("/me", response_model=APIResponse[UserResponse])
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return APIResponse(success=True, data=UserResponse.model_validate(current_user))
