from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración leída del archivo .env o de variables de entorno."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "ReÚsalo Ibero API"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/reusalo"
    jwt_secret: str = "clave-de-desarrollo-cambiala-en-produccion-por-favor"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    allowed_email_domain: str = "iberopuebla.mx"

    # Límites anti-abuso
    max_pending_offers_per_user: int = 5
    max_items_per_offer: int = 3


settings = Settings()
