from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, utcnow



class Role(str, Enum):
    student = "student"
    moderator = "moderator"
    admin = "admin"


class ItemCondition(str, Enum):
    new = "new"
    good = "good"
    used = "used"


class ItemStatus(str, Enum):
    available = "available"  # libre para publicarse u ofrecerse
    committed = "committed"  # publicado u ofrecido en una oferta activa
    exchanged = "exchanged"  # ya cambió de manos


class PostType(str, Enum):
    offer = "offer"  # "doy esto"
    wanted = "wanted"  # "busco esto"


class PostStatus(str, Enum):
    open = "open"
    in_deal = "in_deal"
    completed = "completed"
    closed = "closed"


class OfferStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"  # funciona como acuerdo en espera de entrega
    rejected = "rejected"
    withdrawn = "withdrawn"
    completed = "completed"
    cancelled = "cancelled"


def enum_col(enum_cls):
    return SAEnum(enum_cls, native_enum=False, length=20)



class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(enum_col(Role), default=Role.student)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True)
    # Peso promedio de un artículo de esta categoría, para estimar el impacto.
    avg_weight_kg: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)


class Item(Base):
    """Objeto físico que pertenece a un usuario."""

    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")
    condition: Mapped[ItemCondition] = mapped_column(enum_col(ItemCondition))
    status: Mapped[ItemStatus] = mapped_column(
        enum_col(ItemStatus), default=ItemStatus.available, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Post(Base):
    """Publicación ("doy esto") o pedido ("busco esto").

    - type=offer: item_id es el artículo que se publica (obligatorio).
    - type=wanted: item_id es lo que el autor da a cambio (opcional).
    """

    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True)
    type: Mapped[PostType] = mapped_column(enum_col(PostType), index=True)
    item_id: Mapped[int | None] = mapped_column(ForeignKey("items.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[PostStatus] = mapped_column(
        enum_col(PostStatus), default=PostStatus.open, index=True
    )
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    item: Mapped[Item | None] = relationship(lazy="selectin")


class OfferItem(Base):
    """Artículos incluidos en una oferta (de 1 a 3)."""

    __tablename__ = "offer_items"

    offer_id: Mapped[int] = mapped_column(
        ForeignKey("offers.id", ondelete="CASCADE"), primary_key=True
    )
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), primary_key=True)

    item: Mapped[Item] = relationship(lazy="selectin")


class Offer(Base):
    """Puja o propuesta. Una vez aceptada, funciona como el acuerdo."""

    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), index=True)
    bidder_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    message: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[OfferStatus] = mapped_column(
        enum_col(OfferStatus), default=OfferStatus.pending, index=True
    )
    confirmed_by_author: Mapped[bool] = mapped_column(Boolean, default=False)
    confirmed_by_bidder: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    post: Mapped[Post] = relationship(lazy="selectin")
    offer_items: Mapped[list[OfferItem]] = relationship(
        lazy="selectin", cascade="all, delete-orphan"
    )

    @property
    def items(self) -> list[Item]:
        return [oi.item for oi in self.offer_items]
