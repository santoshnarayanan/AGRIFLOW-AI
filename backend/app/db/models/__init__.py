# Import all ORM models here so Alembic autogenerate detects them.
from app.db.models.crop import Crop
from app.db.models.disease_observation import DiseaseObservation
from app.db.models.farm import Farm
from app.db.models.field import Field
from app.db.models.irrigation_event import IrrigationEvent
from app.db.models.satellite_observation import SatelliteObservation
from app.db.models.sensor_reading import SensorReading
from app.db.models.soil_profile import SoilProfile
from app.db.models.weather_record import WeatherRecord
from app.db.models.yield_record import YieldRecord

__all__ = [
    "Crop",
    "DiseaseObservation",
    "Farm",
    "Field",
    "IrrigationEvent",
    "SatelliteObservation",
    "SensorReading",
    "SoilProfile",
    "WeatherRecord",
    "YieldRecord",
]
