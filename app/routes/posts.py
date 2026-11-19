from fastapi import APIRouter, Depends, Query, status

from app.dependencies import get_current_user, get_offer_repo, get_post_repo, require_role
from app.models import PostStatus, PostType, Role, User
from app.repository import OfferRepository, PostRepository
from app.schemas import OfferCreate, OfferOut, PostCreate, PostOut, PostPage

router = APIRouter(prefix="/posts", tags=["Publicaciones y pedidos"])


@router.get("", response_model=PostPage)
async def list_posts(
    type: PostType | None = None,
    category_id: int | None = None,
    q: str | None = Query(default=None, max_length=100),
    status: PostStatus = PostStatus.open,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    repo: PostRepository = Depends(get_post_repo),
):
    """Listado público con filtros y paginación."""
    total, results = await repo.search(
        type=type, category_id=category_id, q=q, status=status, limit=limit, offset=offset
    )
    return PostPage(total=total, limit=limit, offset=offset, results=results)


@router.post("", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_post(
    data: PostCreate,
    user: User = Depends(get_current_user),
    repo: PostRepository = Depends(get_post_repo),
):
    """Publica un artículo (type=offer) o un pedido (type=wanted)."""
    return await repo.create(user, data)


@router.get("/{post_id}", response_model=PostOut)
async def get_post(post_id: int, repo: PostRepository = Depends(get_post_repo)):
    return await repo.get(post_id)


@router.post("/{post_id}/close", response_model=PostOut)
async def close_post(
    post_id: int,
    user: User = Depends(get_current_user),
    repo: PostRepository = Depends(get_post_repo),
):
    return await repo.close(user, post_id)


@router.patch("/{post_id}/hide", response_model=PostOut)
async def hide_post(
    post_id: int,
    hidden: bool = True,
    _: User = Depends(require_role(Role.moderator)),
    repo: PostRepository = Depends(get_post_repo),
):
    """Moderación: oculta o vuelve a mostrar una publicación."""
    return await repo.set_hidden(post_id, hidden)


@router.post("/{post_id}/offers", response_model=OfferOut, status_code=status.HTTP_201_CREATED)
async def make_offer(
    post_id: int,
    data: OfferCreate,
    user: User = Depends(get_current_user),
    repo: OfferRepository = Depends(get_offer_repo),
):
    """Ofrece de 1 a 3 artículos propios a cambio."""
    return await repo.create(user, post_id, data)
