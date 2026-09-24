from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.user import User
from schemas.user import UserCreate, UserUpdate
from core.security import hash_password, verify_password
# from fastapi import HTTPException

async def authenticate_user(db: AsyncSession, email: str, password: str):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()  # Récupérer le premier utilisateur trouvé

    if user and verify_password(password, user.hashed_password):
        return user
    return None


async def create_user(db: AsyncSession, user: UserCreate):
    db_user = await db.execute(select(User).filter(User.email == user.email))
    if db_user.scalar() is not None:
        return None
    
    hashed_password = hash_password(user.password)
    new_user = User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def get_all_users(db: AsyncSession):
    result = await db.execute(select(User))
    return result.scalars().all()

async def get_user_by_id(db, user_id: int):
    # Attendez l'exécution de la requête
    result = await db.execute(select(User).filter(User.id == user_id))
    # Utilisez scalar_one_or_none pour récupérer le résultat
    return result.scalar_one_or_none()

async def update_user(db: AsyncSession, user_id: int, user_update: UserUpdate) -> User:
    user = await get_user_by_id(db, user_id)
    if not user:
        return None

    if user_update.first_name is not None:
        user.first_name = user_update.first_name
    if user_update.last_name is not None:
        user.last_name = user_update.last_name
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.password is not None:
        user.hashed_password = hash_password(user_update.password)


    await db.commit()
    await db.refresh(user)
    
    return user

async def delete_user(db: AsyncSession, user_id: int):
    user_to_delete = await get_user_by_id(db, user_id)
    if not user_to_delete:
        return None

    await db.delete(user_to_delete)
    await db.commit()
    return user_to_delete
