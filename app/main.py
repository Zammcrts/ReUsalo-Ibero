from fastapi import FastAPI

from app.config import settings
from app.errors import DomainError, domain_error_handler
from app.routes import api_router

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "Marketplace de trueque para la comunidad Ibero Puebla: publica "
        "artículos, recibe ofertas de otros objetos o pide lo que buscas."
    ),
)

app.add_exception_handler(DomainError, domain_error_handler)
app.include_router(api_router)


@app.get("/health", tags=["Sistema"])
async def health():
    return {"status": "ok"}

@app.get("/")
def raiz():
    return {"mensaje": "si funciono muejejeje"}
