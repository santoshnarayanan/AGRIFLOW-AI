# Import all ORM models here so Alembic autogenerate detects them.
from app.db.models.crop import Crop
from app.db.models.farm import Farm
from app.db.models.field import Field
from app.db.models.soil_profile import SoilProfile

__all__ = ["Crop", "Farm", "Field", "SoilProfile"]
