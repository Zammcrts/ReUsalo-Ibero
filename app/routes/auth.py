from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.dependencies import create_access_token, get_user_repo, hash_password, verify_password
from app.errors import Forbidden, Unauthorized
from app.repository import UserRepository
from app.schemas import Token, UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, users: UserRepository = Depends(get_user_repo)):
    """Registro restringido a correos @iberopuebla.mx."""
    return await users.create(data.email, data.full_name, hash_password(data.password))


@router.post("/login", response_model=Token)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    users: UserRepository = Depends(get_user_repo),
):
    """Inicio de sesión. En `username` va el correo institucional."""
    user = await users.get_by_email(form.username)
    if user is None or not verify_password(form.password, user.hashed_password):
        raise Unauthorized("Correo o contraseña incorrectos")
    if not user.is_active:
        raise Forbidden("Cuenta suspendida")
    return Token(access_token=create_access_token(user))
