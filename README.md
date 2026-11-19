<div align="center">

# ReÚsalo Ibero

**API REST para el intercambio de objetos en la comunidad de la Ibero Puebla**

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)
![Alembic](https://img.shields.io/badge/Alembic-migraciones-6BA539?style=for-the-badge)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?style=for-the-badge&logo=pydantic&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-autenticación-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Swagger](https://img.shields.io/badge/Swagger-OpenAPI-85EA2D?style=for-the-badge&logo=swagger&logoColor=black)

Tópicos Avanzados de Cómputo (LIIS1217) · Universidad Iberoamericana Puebla · Otoño 2026

</div>

---

## Descripción

Al concluir cada periodo académico, los estudiantes acumulan libros, calculadoras, material de laboratorio y otros objetos que dejan de utilizar, mientras que otros estudiantes adquieren esos mismos artículos nuevos. El intercambio informal en redes sociales no permite confirmar la disponibilidad de un artículo, comparar ofertas ni registrar el cumplimiento de los compromisos.

ReÚsalo Ibero atiende este problema mediante un marketplace de **trueque**, sin dinero de por medio, en el que cada operación se rige por reglas explícitas y queda registrada en la base de datos. El proyecto se vincula con el eje de sustentabilidad del curso, ya que promueve la reutilización de bienes y estima los residuos evitados.

## Funcionalidades

El sistema contempla dos formas de intercambio que convergen en un mismo flujo de acuerdo:

1. **Publicación con ofertas (`offer`).** Un usuario publica un artículo y otros le ofrecen de uno a tres artículos propios a cambio. El autor elige la oferta que considera conveniente.
2. **Pedido (`wanted`).** Un usuario publica el artículo que busca, con o sin indicar lo que entrega a cambio, y otros responden con una oferta.

Al aceptarse una oferta, las demás se rechazan automáticamente, los artículos involucrados quedan reservados y se comparten los correos de contacto. El intercambio se completa cuando ambas partes confirman la entrega física, momento en el que se actualiza el indicador de impacto.

De manera complementaria, la API ofrece:

- Registro e inicio de sesión con **JWT**, restringidos al dominio `@iberopuebla.mx`.
- Control de acceso con tres roles: **estudiante**, **moderador** y **administrador**.
- Búsqueda de publicaciones por tipo, categoría y texto, con paginación.
- Moderación mediante el ocultamiento de publicaciones y la suspensión de cuentas.
- Un **indicador público de impacto**: artículos reutilizados y kilogramos estimados de residuos evitados.

### Reglas de negocio

| Regla | Mecanismo |
| --- | --- |
| Un artículo solo puede participar en una operación activa a la vez | Estados `available` → `committed` → `exchanged` |
| No se puede ofertar en una publicación propia ni ofrecer artículos ajenos | Validación en la capa de repositorio |
| Máximo cinco ofertas pendientes por usuario | Límite configurable en `config.py` |
| Dos aceptaciones simultáneas no pueden generar dos acuerdos | Transacción única con `SELECT … FOR UPDATE` |
| El intercambio solo se completa con la confirmación de ambas partes | Doble confirmación en la oferta aceptada |

## Arquitectura

La API sigue una arquitectura de monolito modular organizada en capas. Las rutas reciben las peticiones HTTP y delegan la validación en esquemas de Pydantic; el acceso a datos se organiza según el **patrón repositorio**, de modo que las rutas dependen de interfaces abstractas (`repository.py`) y no de la implementación con SQLAlchemy (`repository_sql.py`), donde se concentran las reglas de negocio.

<div align="center">
<img src="docs/diagrama-arquitectura.png" alt="Diagrama de arquitectura" width="850">
</div>

### Modelo de datos

El dominio se representa con seis entidades. Las publicaciones y los pedidos comparten la entidad `Post`, diferenciada por su tipo, y la oferta aceptada funciona como el acuerdo entre las partes.

| Entidad | Función |
| --- | --- |
| `User` | Miembro de la comunidad, con correo institucional y rol |
| `Category` | Clasificación de artículos y peso promedio para estimar el impacto |
| `Item` | Objeto físico de un usuario y su estado |
| `Post` | Publicación de un artículo (`offer`) o pedido (`wanted`) |
| `Offer` | Propuesta de trueque; una vez aceptada, registra las confirmaciones de entrega |
| `OfferItem` | Artículos que componen una oferta (de uno a tres) |

El diagrama entidad-relación completo se encuentra en [`docs/diagrama-er.png`](docs/diagrama-er.png).

### Estructura del repositorio

```
reusalo-ibero/
├── app/
│   ├── routes/            # endpoints: auth, users, catalog, posts, offers
│   ├── config.py          # configuración leída del .env
│   ├── database.py        # conexión asíncrona, sesión y clase Base
│   ├── models.py          # entidades de SQLAlchemy
│   ├── schemas.py         # validación de entrada y salida (Pydantic)
│   ├── repository.py      # interfaces de acceso a datos
│   ├── repository_sql.py  # implementación con SQLAlchemy y reglas de negocio
│   ├── dependencies.py    # JWT, usuario actual, roles y repositorios
│   ├── errors.py          # errores de dominio y su respuesta HTTP
│   └── main.py            # aplicación FastAPI
├── alembic/               # migraciones de la base de datos
├── docs/                  # resumen ejecutivo, diagramas y bitácora
├── docker-compose.yml     # contenedor de PostgreSQL
├── requirements.txt
└── .env.example
```

## Instalación y ejecución

### Requisitos previos

- Python 3.12
- Docker y Docker Compose

### 1. Base de datos en Docker

La base de datos se ejecuta en un contenedor con la imagen oficial `postgres:16-alpine`. Los datos se conservan en un volumen, por lo que persisten al detener el contenedor.

```bash
docker compose up -d
```

El comando crea la base `reusalo` en `localhost:5432`, con usuario y contraseña `postgres`.

### 2. Entorno de Python

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # Windows: copy .env.example .env
```

En el archivo `.env` debe sustituirse `JWT_SECRET` por una cadena larga y aleatoria. La variable `DATABASE_URL` ya apunta al contenedor.

### 3. Migraciones y servidor

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

Una vez iniciado el servidor, la documentación interactiva queda disponible en:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Para autenticarse en Swagger se utiliza el botón **Authorize**, con el correo institucional en el campo `username`.

### 4. Primer administrador

La creación de categorías está reservada al rol de administrador. Tras registrar una cuenta, su rol puede modificarse directamente en la base de datos:

```bash
docker exec -it reusalo-db psql -U postgres -d reusalo \
  -c "update users set role='admin' where email='correo@iberopuebla.mx';"
```

### Detener la base de datos

```bash
docker compose down        # detiene el contenedor y conserva los datos
docker compose down -v     # además elimina el volumen de datos
```

## Endpoints

Todas las rutas se publican bajo el prefijo `/api/v1`, con excepción de `/health`.

| Método | Endpoint | Descripción | Acceso |
|---|---|---|---|
| POST | `/auth/register` | Registro con correo institucional | Público |
| POST | `/auth/login` | Inicio de sesión; devuelve el token JWT | Público |
| GET | `/users/me` | Datos del usuario autenticado | Autenticado |
| PATCH | `/users/{id}/role` | Cambio de rol de un usuario | Administrador |
| PATCH | `/users/{id}/active` | Suspensión o reactivación de una cuenta | Moderador |
| GET | `/categories` | Listado de categorías | Público |
| POST | `/categories` | Creación de una categoría | Administrador |
| GET | `/items/mine` | Artículos del usuario autenticado | Autenticado |
| POST | `/items` | Registro de un artículo | Autenticado |
| DELETE | `/items/{id}` | Eliminación de un artículo disponible | Dueño |
| GET | `/posts` | Búsqueda de publicaciones con filtros y paginación | Público |
| POST | `/posts` | Creación de una publicación (`offer`) o pedido (`wanted`) | Autenticado |
| GET | `/posts/{id}` | Detalle de una publicación | Público |
| POST | `/posts/{id}/close` | Cierre de una publicación | Autor |
| PATCH | `/posts/{id}/hide` | Ocultamiento de una publicación | Moderador |
| POST | `/posts/{id}/offers` | Envío de una oferta de uno a tres artículos | Autenticado |
| GET | `/offers/sent` | Ofertas enviadas | Autenticado |
| GET | `/offers/received` | Ofertas recibidas | Autenticado |
| POST | `/offers/{id}/accept` | Aceptación de una oferta y creación del acuerdo | Autor |
| POST | `/offers/{id}/reject` | Rechazo de una oferta | Autor |
| POST | `/offers/{id}/withdraw` | Retiro de una oferta propia | Ofertante |
| POST | `/offers/{id}/confirm` | Confirmación de la entrega | Partes del acuerdo |
| POST | `/offers/{id}/cancel` | Cancelación de un acuerdo en curso | Partes del acuerdo |
| GET | `/offers/{id}/contact` | Correos de contacto del acuerdo | Partes del acuerdo |
| GET | `/stats/impact` | Indicador de impacto ambiental | Público |
| GET | `/health` | Estado del servicio | Público |

El rol de administrador incluye todos los permisos del moderador.

## Gestión de migraciones

Toda modificación en `app/models.py` debe acompañarse de una migración, de modo que la estructura de la base de datos sea idéntica en cada entorno:

```bash
alembic revision --autogenerate -m "descripción del cambio"
alembic upgrade head      # aplica las migraciones pendientes
alembic downgrade -1      # revierte la última migración
```

El archivo generado en `alembic/versions/` debe revisarse antes de aplicarse, ya que la generación automática no distingue el renombrado de una columna de su eliminación y posterior creación.

## Estado del proyecto

El núcleo funcional de la API se encuentra implementado y fue verificado contra un servidor PostgreSQL mediante una prueba de 14 escenarios, entre ellos la aceptación simultánea de dos ofertas. Para completar los requisitos del curso, resta lo siguiente:

- [ ] Pruebas unitarias y de integración con pytest (cobertura superior al 70%)
- [ ] Dockerfile de la API e integración en `docker-compose.yml`
- [ ] Pipeline de CI/CD con GitHub Actions (black, flake8, pruebas y build)
- [ ] Despliegue en Render o Railway

El detalle cronológico de las decisiones y el trabajo pendiente se documenta en [`docs/bitacora.md`](docs/bitacora.md).

## Documentación

| Documento | Contenido |
| --- | --- |
| [`docs/resumen-ejecutivo.docx`](docs/resumen-ejecutivo.docx) | Problema, objetivo, metodología, resultados y conclusiones |
| [`docs/diagrama-arquitectura.png`](docs/diagrama-arquitectura.png) | Capas de la API y su conexión con PostgreSQL |
| [`docs/diagrama-er.png`](docs/diagrama-er.png) | Modelo entidad-relación de la base de datos |
| [`docs/bitacora.md`](docs/bitacora.md) | Registro de avances, estado actual y trabajo pendiente |

## Limitaciones

- El sistema no verifica el estado físico de los artículos ni garantiza la entrega; depende de la confirmación de ambas partes.
- La verificación de identidad se limita al dominio del correo electrónico.
- El indicador de impacto constituye una estimación basada en el peso promedio de cada categoría, no una medición directa.

## Declaración de uso de inteligencia artificial

De conformidad con la política de transparencia del curso, se declara el uso de un asistente de IA generativa (Claude, de Anthropic) en la generación de ideas, el diseño del modelo de datos, la implementación del código, la redacción de la documentación y la elaboración de los diagramas. La revisión y las modificaciones realizadas por el equipo se detallan en [`docs/bitacora.md`](docs/bitacora.md).
