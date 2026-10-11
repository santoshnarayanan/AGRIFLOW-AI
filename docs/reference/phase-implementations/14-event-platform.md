# Phase 14 — Event platform implementation reference

**Status:** Event platform MVP complete (all catalog producers wired) — ML prediction engines & replay tooling remain roadmap  
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

## Delivered (slice 4 — idempotency, tests, frontend)

| Component | Location |
|-----------|----------|
| Consumer idempotency | `domain_event_consumer_inbox` migration `j4k5l6m7n8o9` |
| Business consumer dedup | `DomainEventConsumerInboxRepository.try_claim` in `business_consumer.py` |
| Envelope contract test | `backend/app/tests/test_domain_event_envelope.py` |
| Outbox stats extension | `events_processed` on `GET /events/outbox/stats` |
| React UI | `/events` — catalog table, outbox stats, outbox entries (`frontend/src/pages/Events.tsx`) |

## Delivered (slice 5 — decision intelligence producers)

| Producer event | Service trigger |
|----------------|-----------------|
| `RecommendationCreated` | `RecommendationService.create_recommendation` |
| `AlertTriggered` | `AlertService.create_alert` (API and alert-evaluation consumer when `EVENTS_ENABLED`) |

Topics: `agriflow.domain.recommendation-created.v1`, `agriflow.domain.alert-triggered.v1`.

## Remaining (optional / Phase 15+)

- Event replay / backfill tooling
- Formal schema versioning policy and compatibility CI
- Predictive ML engines (roadmap near-term; not part of event-platform MVP)
- Auth on outbox ops endpoints
