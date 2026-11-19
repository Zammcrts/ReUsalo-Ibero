from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.errors import Conflict, DomainError, Forbidden, NotFound
from app.models import (
    Category,
    Item,
    ItemStatus,
    Offer,
    OfferItem,
    OfferStatus,
    Post,
    PostStatus,
    PostType,
    User,
)
from app.repository import (
    CatalogRepository,
    OfferRepository,
    PostRepository,
    UserRepository,
)
from app.schemas import CategoryCreate, ItemCreate, OfferCreate, PostCreate



async def lock_available_items(db: AsyncSession, owner: User, item_ids: list[int]) -> list[Item]:
    """Bloquea (FOR UPDATE) y valida artículos antes de comprometerlos."""
    items = list(await db.scalars(select(Item).where(Item.id.in_(item_ids)).with_for_update()))
    if len(items) != len(set(item_ids)):
        raise NotFound("Alguno de los artículos no existe")
    for item in items:
        if item.owner_id != owner.id:
            raise Forbidden(f"El artículo {item.id} no te pertenece")
        if item.status != ItemStatus.available:
            raise Conflict(f"El artículo {item.id} no está disponible")
    return items


def set_status(items: list[Item], status: ItemStatus) -> None:
    for item in items:
        item.status = status


async def lock_post(db: AsyncSession, post_id: int) -> Post:
    post = await db.scalar(
        select(Post)
        .where(Post.id == post_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if post is None:
        raise NotFound("Publicación no encontrada")
    return post




class SqlUserRepository(UserRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, user_id: int) -> User:
        user = await self.db.get(User, user_id)
        if user is None:
            raise NotFound("Usuario no encontrado")
        return user

    async def get_by_email(self, email: str) -> User | None:
        return await self.db.scalar(select(User).where(User.email == email.lower()))

    async def create(self, email: str, full_name: str, hashed_password: str) -> User:
        if await self.get_by_email(email):
            raise Conflict("Ya existe una cuenta con ese correo")
        user = User(email=email, full_name=full_name, hashed_password=hashed_password)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def save(self, user: User) -> User:
        await self.db.commit()
        await self.db.refresh(user)
        return user



class SqlCatalogRepository(CatalogRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_categories(self) -> list[Category]:
        return list(await self.db.scalars(select(Category).order_by(Category.name)))

    async def create_category(self, data: CategoryCreate) -> Category:
        if await self.db.scalar(select(Category).where(Category.name == data.name)):
            raise Conflict("La categoría ya existe")
        category = Category(**data.model_dump())
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def create_item(self, owner: User, data: ItemCreate) -> Item:
        if await self.db.get(Category, data.category_id) is None:
            raise DomainError("La categoría no existe")
        item = Item(owner_id=owner.id, **data.model_dump())
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def list_items_of(self, owner: User) -> list[Item]:
        stmt = select(Item).where(Item.owner_id == owner.id).order_by(Item.id.desc())
        return list(await self.db.scalars(stmt))

    async def delete_item(self, owner: User, item_id: int) -> None:
        item = await self.db.get(Item, item_id)
        if item is None:
            raise NotFound("Artículo no encontrado")
        if item.owner_id != owner.id:
            raise Forbidden("El artículo no te pertenece")
        if item.status != ItemStatus.available:
            raise Conflict("No puedes borrar un artículo publicado, ofrecido o cambiado")
        await self.db.delete(item)
        await self.db.commit()




class SqlPostRepository(PostRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, author: User, data: PostCreate) -> Post:
        item = None
        if data.item_id is not None:
            [item] = await lock_available_items(self.db, author, [data.item_id])

        if data.type == PostType.offer:
            category_id = item.category_id
        else:
            category_id = data.category_id
            if await self.db.get(Category, category_id) is None:
                raise DomainError("La categoría no existe")

        post = Post(
            author_id=author.id,
            category_id=category_id,
            type=data.type,
            item_id=item.id if item else None,
            title=data.title,
            description=data.description,
        )
        if item:
            item.status = ItemStatus.committed
        self.db.add(post)
        await self.db.commit()
        await self.db.refresh(post)
        return post

    async def get(self, post_id: int) -> Post:
        post = await self.db.get(Post, post_id)
        if post is None or post.is_hidden:
            raise NotFound("Publicación no encontrada")
        return post

    async def search(self, *, type, category_id, q, status, limit, offset):
        filters = [Post.is_hidden.is_(False), Post.status == status]
        if type:
            filters.append(Post.type == type)
        if category_id:
            filters.append(Post.category_id == category_id)
        if q:
            filters.append(or_(Post.title.ilike(f"%{q}%"), Post.description.ilike(f"%{q}%")))

        total = await self.db.scalar(select(func.count()).select_from(Post).where(*filters))
        results = await self.db.scalars(
            select(Post)
            .where(*filters)
            .order_by(Post.created_at.desc(), Post.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return total or 0, list(results)

    async def close(self, author: User, post_id: int) -> Post:
        """Cierra la publicación, rechaza ofertas pendientes y libera artículos."""
        post = await lock_post(self.db, post_id)
        if post.author_id != author.id:
            raise Forbidden("Solo el autor puede cerrar la publicación")
        if post.status != PostStatus.open:
            raise Conflict("Solo se pueden cerrar publicaciones abiertas")

        pending = await self.db.scalars(
            select(Offer).where(Offer.post_id == post.id, Offer.status == OfferStatus.pending)
        )
        for offer in pending:
            offer.status = OfferStatus.rejected
            set_status(offer.items, ItemStatus.available)
        if post.item:
            post.item.status = ItemStatus.available
        post.status = PostStatus.closed
        await self.db.commit()
        await self.db.refresh(post)
        return post

    async def set_hidden(self, post_id: int, hidden: bool) -> Post:
        post = await self.db.get(Post, post_id)
        if post is None:
            raise NotFound("Publicación no encontrada")
        post.is_hidden = hidden
        await self.db.commit()
        await self.db.refresh(post)
        return post



class SqlOfferRepository(OfferRepository):
    """pending -> accepted | rejected | withdrawn ; accepted -> completed | cancelled"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get(self, offer_id: int, lock: bool = False) -> Offer:
        stmt = select(Offer).where(Offer.id == offer_id)
        if lock:
            stmt = stmt.with_for_update()
        offer = await self.db.scalar(stmt)
        if offer is None:
            raise NotFound("Oferta no encontrada")
        return offer

    async def _lock_offer_and_post(self, offer_id: int) -> tuple[Offer, Post]:
        """Bloquea primero la publicación y luego la oferta (siempre en ese
        orden, para evitar bloqueos cruzados)."""
        offer = await self._get(offer_id)
        post = await lock_post(self.db, offer.post_id)
        return await self._get(offer_id, lock=True), post

    @staticmethod
    def _party(offer: Offer, user: User) -> str:
        if user.id == offer.post.author_id:
            return "author"
        if user.id == offer.bidder_id:
            return "bidder"
        raise Forbidden("No eres parte de este acuerdo")

    async def create(self, bidder: User, post_id: int, data: OfferCreate) -> Offer:
        post = await self.db.get(Post, post_id)
        if post is None or post.is_hidden:
            raise NotFound("Publicación no encontrada")
        if post.status != PostStatus.open:
            raise Conflict("La publicación ya no recibe ofertas")
        if post.author_id == bidder.id:
            raise DomainError("No puedes ofertar en tu propia publicación")

        mine_pending = select(Offer).where(
            Offer.bidder_id == bidder.id, Offer.status == OfferStatus.pending
        )
        if await self.db.scalar(mine_pending.where(Offer.post_id == post.id)):
            raise Conflict("Ya tienes una oferta pendiente en esta publicación")
        count = await self.db.scalar(select(func.count()).select_from(mine_pending.subquery()))
        if count >= settings.max_pending_offers_per_user:
            raise Conflict(f"Máximo {settings.max_pending_offers_per_user} ofertas pendientes")

        items = await lock_available_items(self.db, bidder, data.item_ids)
        offer = Offer(
            post_id=post.id,
            bidder_id=bidder.id,
            message=data.message,
            offer_items=[OfferItem(item_id=i.id) for i in items],
        )
        set_status(items, ItemStatus.committed)
        self.db.add(offer)
        await self.db.commit()
        return await self._get(offer.id)

    async def list_sent(self, user: User) -> list[Offer]:
        stmt = select(Offer).where(Offer.bidder_id == user.id).order_by(Offer.id.desc())
        return list(await self.db.scalars(stmt))

    async def list_received(self, user: User) -> list[Offer]:
        stmt = (
            select(Offer)
            .join(Post, Post.id == Offer.post_id)
            .where(Post.author_id == user.id)
            .order_by(Offer.id.desc())
        )
        return list(await self.db.scalars(stmt))

    async def accept(self, author: User, offer_id: int) -> Offer:
        """Acepta una oferta en UNA transacción: la publicación queda bloqueada,
        así que si llegan dos aceptaciones a la vez, solo una se completa."""
        offer, post = await self._lock_offer_and_post(offer_id)
        if post.author_id != author.id:
            raise Forbidden("Solo el autor de la publicación puede aceptar ofertas")
        if post.status != PostStatus.open:
            raise Conflict("La publicación ya no está abierta")
        if offer.status != OfferStatus.pending:
            raise Conflict("La oferta ya no está pendiente")

        offer.status = OfferStatus.accepted
        post.status = PostStatus.in_deal
        others = await self.db.scalars(
            select(Offer).where(
                Offer.post_id == post.id,
                Offer.status == OfferStatus.pending,
                Offer.id != offer.id,
            )
        )
        for other in others:
            other.status = OfferStatus.rejected
            set_status(other.items, ItemStatus.available)

        await self.db.commit()
        return await self._get(offer.id)

    async def reject(self, author: User, offer_id: int) -> Offer:
        offer = await self._get(offer_id, lock=True)
        if offer.post.author_id != author.id:
            raise Forbidden("Solo el autor de la publicación puede rechazar ofertas")
        if offer.status != OfferStatus.pending:
            raise Conflict("La oferta ya no está pendiente")
        offer.status = OfferStatus.rejected
        set_status(offer.items, ItemStatus.available)
        await self.db.commit()
        return await self._get(offer.id)

    async def withdraw(self, bidder: User, offer_id: int) -> Offer:
        offer = await self._get(offer_id, lock=True)
        if offer.bidder_id != bidder.id:
            raise Forbidden("Solo quien hizo la oferta puede retirarla")
        if offer.status != OfferStatus.pending:
            raise Conflict("Solo se pueden retirar ofertas pendientes")
        offer.status = OfferStatus.withdrawn
        set_status(offer.items, ItemStatus.available)
        await self.db.commit()
        return await self._get(offer.id)

    async def confirm(self, user: User, offer_id: int) -> Offer:
        """Cada parte confirma la entrega; con ambas se completa el intercambio."""
        offer, post = await self._lock_offer_and_post(offer_id)
        party = self._party(offer, user)
        if offer.status != OfferStatus.accepted:
            raise Conflict("La oferta no está en acuerdo")

        if party == "author":
            offer.confirmed_by_author = True
        else:
            offer.confirmed_by_bidder = True

        if offer.confirmed_by_author and offer.confirmed_by_bidder:
            offer.status = OfferStatus.completed
            post.status = PostStatus.completed
            set_status(offer.items, ItemStatus.exchanged)
            if post.item:
                post.item.status = ItemStatus.exchanged

        await self.db.commit()
        return await self._get(offer.id)

    async def cancel(self, user: User, offer_id: int) -> Offer:
        """Cancela un acuerdo en curso: la publicación se reabre."""
        offer, post = await self._lock_offer_and_post(offer_id)
        self._party(offer, user)
        if offer.status != OfferStatus.accepted:
            raise Conflict("Solo se pueden cancelar acuerdos en curso")
        offer.status = OfferStatus.cancelled
        post.status = PostStatus.open
        set_status(offer.items, ItemStatus.available)
        await self.db.commit()
        return await self._get(offer.id)

    async def contact(self, user: User, offer_id: int) -> dict:
        offer = await self._get(offer_id)
        self._party(offer, user)
        if offer.status not in (OfferStatus.accepted, OfferStatus.completed):
            raise Conflict("El contacto solo se comparte en acuerdos aceptados")
        author = await self.db.get(User, offer.post.author_id)
        bidder = await self.db.get(User, offer.bidder_id)
        return {"offer": offer, "author_email": author.email, "bidder_email": bidder.email}

    async def impact(self) -> dict:
        """Artículos intercambiados × peso promedio de su categoría."""
        exchanges = await self.db.scalar(
            select(func.count()).select_from(Offer).where(Offer.status == OfferStatus.completed)
        )
        rows = await self.db.execute(
            select(Category.name, func.count(Item.id), func.sum(Category.avg_weight_kg))
            .join(Item, Item.category_id == Category.id)
            .where(Item.status == ItemStatus.exchanged)
            .group_by(Category.name)
            .order_by(func.count(Item.id).desc())
        )
        by_category = [
            {
                "category": name,
                "items_exchanged": count,
                "kg_avoided": Decimal(kg).quantize(Decimal("0.01")),
            }
            for name, count, kg in rows
        ]
        return {
            "exchanges_completed": exchanges or 0,
            "items_exchanged": sum(c["items_exchanged"] for c in by_category),
            "kg_avoided": sum((c["kg_avoided"] for c in by_category), Decimal("0.00")),
            "by_category": by_category,
        }
