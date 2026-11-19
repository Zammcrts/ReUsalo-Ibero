from abc import ABC, abstractmethod

from app.models import Category, Item, Offer, Post, PostStatus, PostType, User
from app.schemas import CategoryCreate, ItemCreate, OfferCreate, PostCreate


class UserRepository(ABC):
    @abstractmethod
    async def get(self, user_id: int) -> User: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def create(self, email: str, full_name: str, hashed_password: str) -> User: ...

    @abstractmethod
    async def save(self, user: User) -> User: ...


class CatalogRepository(ABC):
    @abstractmethod
    async def list_categories(self) -> list[Category]: ...

    @abstractmethod
    async def create_category(self, data: CategoryCreate) -> Category: ...

    @abstractmethod
    async def create_item(self, owner: User, data: ItemCreate) -> Item: ...

    @abstractmethod
    async def list_items_of(self, owner: User) -> list[Item]: ...

    @abstractmethod
    async def delete_item(self, owner: User, item_id: int) -> None: ...


class PostRepository(ABC):
    @abstractmethod
    async def create(self, author: User, data: PostCreate) -> Post: ...

    @abstractmethod
    async def get(self, post_id: int) -> Post: ...

    @abstractmethod
    async def search(
        self,
        *,
        type: PostType | None,
        category_id: int | None,
        q: str | None,
        status: PostStatus,
        limit: int,
        offset: int,
    ) -> tuple[int, list[Post]]: ...

    @abstractmethod
    async def close(self, author: User, post_id: int) -> Post: ...

    @abstractmethod
    async def set_hidden(self, post_id: int, hidden: bool) -> Post: ...


class OfferRepository(ABC):
    @abstractmethod
    async def create(self, bidder: User, post_id: int, data: OfferCreate) -> Offer: ...

    @abstractmethod
    async def list_sent(self, user: User) -> list[Offer]: ...

    @abstractmethod
    async def list_received(self, user: User) -> list[Offer]: ...

    @abstractmethod
    async def accept(self, author: User, offer_id: int) -> Offer: ...

    @abstractmethod
    async def reject(self, author: User, offer_id: int) -> Offer: ...

    @abstractmethod
    async def withdraw(self, bidder: User, offer_id: int) -> Offer: ...

    @abstractmethod
    async def confirm(self, user: User, offer_id: int) -> Offer: ...

    @abstractmethod
    async def cancel(self, user: User, offer_id: int) -> Offer: ...

    @abstractmethod
    async def contact(self, user: User, offer_id: int) -> dict: ...

    @abstractmethod
    async def impact(self) -> dict: ...
