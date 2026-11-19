"""Dependencias de FastAPI: seguridad (hash y JWT), usuario actual,
control de roles y creación de los repositorios."""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.errors import Forbidden, Unauthorized
from app.models import Role, User
from app.repository import (
    CatalogRepository,
    OfferRepository,
    PostRepository,
    UserRepository,
)
from app.repository_sql import (
    SqlCatalogRepository,
    SqlOfferRepository,
    SqlPostRepository,
    SqlUserRepository,
)

# ---------- Contraseñas y tokens ----------


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_access_token(user: User) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user.id), "role": user.role.value, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


# ---------- Repositorios ----------


def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return SqlUserRepository(db)


def get_catalog_repo(db: AsyncSession = Depends(get_db)) -> CatalogRepository:
    return SqlCatalogRepository(db)


def get_post_repo(db: AsyncSession = Depends(get_db)) -> PostRepository:
    return SqlPostRepository(db)


def get_offer_repo(db: AsyncSession = Depends(get_db)) -> OfferRepository:
    return SqlOfferRepository(db)


# ---------- Usuario actual y roles ----------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    users: UserRepository = Depends(get_user_repo),
) -> User:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user = await users.get(int(payload["sub"]))
    except Exception:
        raise Unauthorized("Token inválido o expirado")
    if not user.is_active:
        raise Forbidden("Cuenta suspendida")
    return user


def require_role(*roles: Role):
    """Exige uno de los roles indicados. El administrador siempre pasa."""

    async def checker(user: User = Depends(get_current_user)) -> User:
        if user.role != Role.admin and user.role not in roles:
            raise Forbidden("Permisos insuficientes")
        return user

    return checker
