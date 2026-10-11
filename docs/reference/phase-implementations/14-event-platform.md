# Phase 14 — Event platform implementation reference (in progress)

**Status:** Started — transactional outbox + first producer  
**ADR:** [ADR-006](../../../adr/ADR-006-domain-events-transactional-outbox.md)  
**Migration:** `i3j4k5l6m7n8` (`domain_event_outbox`)

## Delivered (slice 1 — outbox foundation)

| Component | Location |
|-----------|----------|
| Event types & catalog | `backend/app/events/types.py`, `catalog.py` |
| Payload schemas | `backend/app/events/schemas.py` |
| Outbox ORM | `backend/app/db/models/domain_event_outbox.py` |
| Outbox repository | `backend/app/db/repositories/domain_event_outbox.py` |
| Outbox publisher | `backend/app/events/publisher.py` |
| Relay worker | `backend/app/events/relay.py` (`python -m app.events.relay`) |
| Catalog API | `GET /api/v1/events/catalog` |
| First producer | `SensorReadingService.create_sensor_reading` → `SensorReadingCreated` |
| Compose | `redpanda`, `outbox-relay` services in `docker-compose.yml` |

## Configuration

See `backend/.env.example` — `EVENTS_ENABLED`, `REDPANDA_ENABLED`, `REDPANDA_BROKERS`.

## Delivered (slice 2 — producers + audit consumer)

| Producer event | Service trigger |
|----------------|-----------------|
| `SensorReadingCreated` | `SensorReadingService.create_sensor_reading` |
| `WeatherRecordCreated` | `WeatherRecordService.create_weather_record` |
| `IrrigationCompleted` | create when `ended_at` set; update when `ended_at` first set |
| `YieldRecorded` | `YieldRecordService.create_yield_record` |
| `DiseaseObserved` | `DiseaseObservationService.create_observation` |
| `SatelliteObserved` | `SatelliteObservationService.create_satellite_observation` |
| `CropLifecycleChanged` | `CropService.update_crop` when `status` changes |

| Component | Location |
|-----------|----------|
| Audit consumer | `python -m app.events.consumer` |
| Compose service | `event-audit-consumer` |

Shared DI: `DomainEventPublisherDep` in `app/api/deps.py`.

## Delivered (slice 3 — ops API + alert evaluation consumer)

| API | Purpose |
|-----|---------|
| `GET /api/v1/events/outbox/stats` | Pending / published / failed counts |
| `GET /api/v1/events/outbox/entries` | Filter `pending` \| `published` \| `failed` \| `all` |
| `GET /api/v1/events/outbox/entries/{id}` | Single outbox row |

| Consumer | Behavior |
|----------|----------|
| `python -m app.events.business_consumer` | `SensorReadingCreated` + `SOIL_MOISTURE` below threshold → `SOIL_MOISTURE_LOW` alert (deduped if one is already open) |
| Compose | `alert-evaluation-consumer` |

Config: `ALERT_EVALUATION_ENABLED`, `SOIL_MOISTURE_LOW_THRESHOLD_PERCENT`, `REDPANDA_BUSINESS_CONSUMER_GROUP_ID`.

## Next slices

- Phase 14 frontend (catalog + outbox ops screens)
- Consumer idempotency store (`event_id` processed log)
- Contract tests for envelope JSON
