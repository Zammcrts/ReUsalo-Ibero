from fastapi import APIRouter, Depends, Response, status

from app.dependencies import get_catalog_repo, get_current_user, require_role
from app.models import Role, User
from app.repository import CatalogRepository
from app.schemas import CategoryCreate, CategoryOut, ItemCreate, ItemOut

router = APIRouter(tags=["Categorías y artículos"])


@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(repo: CatalogRepository = Depends(get_catalog_repo)):
    return await repo.list_categories()


@router.post("/categories", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    _: User = Depends(require_role(Role.admin)),
    repo: CatalogRepository = Depends(get_catalog_repo),
):
    return await repo.create_category(data)


@router.get("/items/mine", response_model=list[ItemOut])
async def my_items(
    user: User = Depends(get_current_user),
    repo: CatalogRepository = Depends(get_catalog_repo),
):
    return await repo.list_items_of(user)


@router.post("/items", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
async def create_item(
    data: ItemCreate,
    user: User = Depends(get_current_user),
    repo: CatalogRepository = Depends(get_catalog_repo),
):
    return await repo.create_item(user, data)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    user: User = Depends(get_current_user),
    repo: CatalogRepository = Depends(get_catalog_repo),
):
    await repo.delete_item(user, item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
