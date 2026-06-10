# Crehana Task Manager

API REST para gestión de listas de tareas y tareas. Desafío técnico backend Crehana.

Las decisiones técnicas detrás del diseño están documentadas en [DECISION_LOG.md](./DECISION_LOG.md).

## Stack

- Python 3.12 + FastAPI + Pydantic v2
- PostgreSQL + SQLAlchemy 2 (async) + asyncpg
- uv (gestor de paquetes)
- pytest + pytest-asyncio (testing)
- flake8 + black + isort + ruff (linting y formateo)
- Docker + docker-compose

## Setup local

### Prerequisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) instalado
- PostgreSQL corriendo localmente (o usar Docker)

### Instalación

```bash
# Clonar el repositorio
git clone <url>
cd prueba_crehana

# Instalar dependencias (crea .venv automáticamente)
uv sync --group dev

# Copiar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales de PostgreSQL
```

### Correr la aplicación

```bash
uv run uvicorn src.main:app --reload
```

La API estará disponible en `http://localhost:8000`.
Documentación interactiva: `http://localhost:8000/docs`

## Docker

```bash
# Levantar app + PostgreSQL
docker compose up --build

# Solo la base de datos (para desarrollo local)
docker compose up db
```

## Tests

El proyecto tiene **116 tests** con **90.9% de cobertura** de línea, distribuidos en dos capas:

| Capa | Tests | Qué cubren |
|------|-------|------------|
| Unitarios | 86 | Servicios y controladores con mocks — lógica de negocio aislada de la DB |
| Integración | 30 | Flujo completo HTTP → DB real (`crehana_test`) — autenticación, CRUD, paginación, contador de tareas |

```
---------- coverage: 90.92% ----------
src/controllers/     100%
src/routers/         100%
src/schemas/         100%
src/services/        100%
src/repositories/     ~70% (cubierto por integración)
```

### Correr los tests

```bash
# Todos los tests con reporte de cobertura
uv run pytest

# Solo unitarios (rápidos, sin DB)
uv run pytest tests/unit/ -v

# Solo integración (requiere PostgreSQL en puerto 5434)
uv run pytest tests/integration/ -v

# Ver cobertura en HTML
uv run pytest --cov-report=html && open htmlcov/index.html
```

### Requisito para integración

Los tests de integración usan una base de datos separada (`crehana_test`) que se crea automáticamente. Solo necesitan PostgreSQL corriendo:

```bash
# Levantar solo la DB con Docker
docker compose up db
```

## Linting y formateo

```bash
# Formatear código
uv run black src/ tests/
uv run isort src/ tests/

# Linter
uv run flake8 src/ tests/
uv run ruff check src/ tests/
```
