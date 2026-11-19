from fastapi import APIRouter, Depends

from app.dependencies import get_current_user, get_offer_repo
from app.models import User
from app.repository import OfferRepository
from app.schemas import DealContact, ImpactOut, OfferOut

router = APIRouter(tags=["Ofertas y acuerdos"])


@router.get("/offers/sent", response_model=list[OfferOut])
async def sent(
    user: User = Depends(get_current_user), repo: OfferRepository = Depends(get_offer_repo)
):
    return await repo.list_sent(user)


@router.get("/offers/received", response_model=list[OfferOut])
async def received(
    user: User = Depends(get_current_user), repo: OfferRepository = Depends(get_offer_repo)
):
    return await repo.list_received(user)


@router.post("/offers/{offer_id}/accept", response_model=OfferOut)
async def accept(
    offer_id: int,
    user: User = Depends(get_current_user),
    repo: OfferRepository = Depends(get_offer_repo),
):
    """El autor acepta: se crea el acuerdo y se rechazan las demás ofertas."""
    return await repo.accept(user, offer_id)


@router.post("/offers/{offer_id}/reject", response_model=OfferOut)
async def reject(
    offer_id: int,
    user: User = Depends(get_current_user),
    repo: OfferRepository = Depends(get_offer_repo),
):
    return await repo.reject(user, offer_id)


@router.post("/offers/{offer_id}/withdraw", response_model=OfferOut)
async def withdraw(
    offer_id: int,
    user: User = Depends(get_current_user),
    repo: OfferRepository = Depends(get_offer_repo),
):
    return await repo.withdraw(user, offer_id)


@router.post("/offers/{offer_id}/confirm", response_model=OfferOut)
async def confirm(
    offer_id: int,
    user: User = Depends(get_current_user),
    repo: OfferRepository = Depends(get_offer_repo),
):
    """Cada parte confirma la entrega; con ambas se completa el intercambio."""
    return await repo.confirm(user, offer_id)


@router.post("/offers/{offer_id}/cancel", response_model=OfferOut)
async def cancel(
    offer_id: int,
    user: User = Depends(get_current_user),
    repo: OfferRepository = Depends(get_offer_repo),
):
    return await repo.cancel(user, offer_id)


@router.get("/offers/{offer_id}/contact", response_model=DealContact)
async def contact(
    offer_id: int,
    user: User = Depends(get_current_user),
    repo: OfferRepository = Depends(get_offer_repo),
):
    """Correos de ambas partes, visibles solo dentro de un acuerdo."""
    return await repo.contact(user, offer_id)


@router.get("/stats/impact", response_model=ImpactOut, tags=["Impacto"])
async def impact(repo: OfferRepository = Depends(get_offer_repo)):
    """Indicador público: intercambios, artículos reusados y kg estimados evitados."""
    return await repo.impact()
