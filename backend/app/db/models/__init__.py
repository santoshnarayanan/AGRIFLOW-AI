# Import all ORM models here so Alembic autogenerate detects them.
from app.db.models.alert import Alert
from app.db.models.crop import Crop
from app.db.models.domain_event_consumer_inbox import DomainEventConsumerInbox
from app.db.models.domain_event_outbox import DomainEventOutbox
from app.db.models.disease_observation import DiseaseObservation
from app.db.models.farm import Farm
from app.db.models.field import Field
from app.db.models.field_feature_snapshot import FieldFeatureSnapshot
from app.db.models.irrigation_event import IrrigationEvent
from app.db.models.recommendation import Recommendation
from app.db.models.satellite_observation import SatelliteObservation
from app.db.models.sensor_reading import SensorReading
from app.db.models.soil_profile import SoilProfile
from app.db.models.weather_record import WeatherRecord
from app.db.models.yield_record import YieldRecord

__all__ = [
    "Alert",
    "Crop",
    "DomainEventConsumerInbox",
    "DomainEventOutbox",
    "DiseaseObservation",
    "Farm",
    "Field",
    "FieldFeatureSnapshot",
    "IrrigationEvent",
    "Recommendation",
    "SatelliteObservation",
    "SensorReading",
    "SoilProfile",
    "WeatherRecord",
    "YieldRecord",
]
