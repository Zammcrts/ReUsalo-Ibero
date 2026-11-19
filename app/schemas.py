from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.config import settings
from app.models import ItemCondition, ItemStatus, OfferStatus, PostStatus, PostType, Role

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=72)

    @field_validator("email")
    @classmethod
    def institutional_domain(cls, v: str) -> str:
        if not v.lower().endswith("@" + settings.allowed_email_domain):
            raise ValueError(f"Solo se permiten correos @{settings.allowed_email_domain}")
        return v.lower()


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: Role
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RoleUpdate(BaseModel):
    role: Role


class ActiveUpdate(BaseModel):
    is_active: bool



class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=60)
    avg_weight_kg: Decimal = Field(ge=0, le=9999)


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    avg_weight_kg: Decimal


class ItemCreate(BaseModel):
    category_id: int
    title: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=2000)
    condition: ItemCondition


class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    category_id: int
    title: str
    description: str
    condition: ItemCondition
    status: ItemStatus
    created_at: datetime



class PostCreate(BaseModel):
    type: PostType
    title: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=2000)
    item_id: int | None = None  # offer: lo que publico · wanted: lo que doy a cambio
    category_id: int | None = None  # solo wanted: categoría de lo que busco

    @model_validator(mode="after")
    def check_by_type(self):
        if self.type == PostType.offer and self.item_id is None:
            raise ValueError("Una publicación de tipo offer requiere item_id")
        if self.type == PostType.wanted and self.category_id is None:
            raise ValueError("Un pedido de tipo wanted requiere category_id")
        return self


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    author_id: int
    category_id: int
    type: PostType
    title: str
    description: str
    status: PostStatus
    item: ItemOut | None
    created_at: datetime


class PostPage(BaseModel):
    total: int
    limit: int
    offset: int
    results: list[PostOut]


class OfferCreate(BaseModel):
    item_ids: list[int] = Field(min_length=1, max_length=settings.max_items_per_offer)
    message: str = Field(default="", max_length=1000)

    @model_validator(mode="after")
    def unique_items(self):
        if len(set(self.item_ids)) != len(self.item_ids):
            raise ValueError("No repitas artículos en la misma oferta")
        return self


class OfferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    post_id: int
    bidder_id: int
    message: str
    status: OfferStatus
    confirmed_by_author: bool
    confirmed_by_bidder: bool
    items: list[ItemOut]
    created_at: datetime


class DealContact(BaseModel):
    offer: OfferOut
    author_email: str
    bidder_email: str



class CategoryImpact(BaseModel):
    category: str
    items_exchanged: int
    kg_avoided: Decimal


class ImpactOut(BaseModel):
    exchanges_completed: int
    items_exchanged: int
    kg_avoided: Decimal
    by_category: list[CategoryImpact]
