# Import all ORM models here so Alembic autogenerate detects them.
from app.db.models.farm import Farm

__all__ = ["Farm"]
