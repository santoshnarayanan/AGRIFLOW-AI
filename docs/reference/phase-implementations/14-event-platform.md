# Phase 14 — Event platform implementation reference (in progress)

**Status:** Started — transactional outbox + first producer  
**ADR:** [ADR-006](../../../adr/ADR-006-domain-events-transactional-outbox.md)  
**Migration:** `i3j4k5l6m7n8` (`domain_event_outbox`)

## Delivered (slice 1)

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

## Next slices

- Wire remaining domain services (yield, disease, irrigation, …)
- Event consumers (alert evaluation stub)
- Contract tests for envelope JSON
