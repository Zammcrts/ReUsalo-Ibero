from fastapi import APIRouter, Depends

from app.dependencies import get_current_user, get_user_repo, require_role
from app.models import Role, User
from app.repository import UserRepository
from app.schemas import ActiveUpdate, RoleUpdate, UserOut

router = APIRouter(prefix="/users", tags=["Usuarios"])


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user


@router.patch("/{user_id}/role", response_model=UserOut)
async def change_role(
    user_id: int,
    data: RoleUpdate,
    _: User = Depends(require_role(Role.admin)),
    users: UserRepository = Depends(get_user_repo),
):
    """Solo administradores."""
    user = await users.get(user_id)
    user.role = data.role
    return await users.save(user)


@router.patch("/{user_id}/active", response_model=UserOut)
async def set_active(
    user_id: int,
    data: ActiveUpdate,
    _: User = Depends(require_role(Role.moderator)),
    users: UserRepository = Depends(get_user_repo),
):
    """Suspender o reactivar una cuenta. Moderadores y administradores."""
    user = await users.get(user_id)
    user.is_active = data.is_active
    return await users.save(user)
