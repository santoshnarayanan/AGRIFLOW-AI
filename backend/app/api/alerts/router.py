"""
Alert API router.

Alerts are the real-time notification layer of Phase 13 — they surface urgent
conditions (soil moisture crossing thresholds, disease risk spikes, frost events)
that require operator attention or immediate action.

Delivered endpoints:
    POST   /fields/{field_id}/alerts        — create an alert
    GET    /fields/{field_id}/alerts        — list all alerts for a field
    GET    /fields/{field_id}/alerts/active — list only unacknowledged alerts
    GET    /alerts/{alert_id}               — get a single alert by ID
    PATCH  /alerts/{alert_id}              — partial update / acknowledge
    DELETE /alerts/{alert_id}              — delete
"""

import uuid

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import AlertServiceDep
from app.schemas.alert import AlertCreate, AlertResponse, AlertUpdate
from app.services.alert import (
    AlertNotFoundError,
    AlertRecommendationMismatchError,
    InvalidAlertError,
)
from app.services.field import FieldNotFoundError

router = APIRouter(tags=["alerts"])


@router.post(
    "/fields/{field_id}/alerts",
    response_model=AlertResponse,
    status_code=201,
)
async def create_alert(
    field_id: uuid.UUID,
    payload: AlertCreate,
    alert_service: AlertServiceDep,
) -> AlertResponse:
    """Create a new alert for a field."""
    try:
        alert = await alert_service.create_alert(field_id, payload)
    except FieldNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AlertRecommendationMismatchError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except InvalidAlertError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return AlertResponse.model_validate(alert)


@router.get(
    "/fields/{field_id}/alerts",
    response_model=list[AlertResponse],
)
async def list_field_alerts(
    field_id: uuid.UUID,
    alert_service: AlertServiceDep,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[AlertResponse]:
    """List all alerts for a field, newest first."""
    alerts = await alert_service.list_field_alerts(
        field_id, limit=limit, offset=offset
    )
    return [AlertResponse.model_validate(a) for a in alerts]


@router.get(
    "/fields/{field_id}/alerts/active",
    response_model=list[AlertResponse],
)
async def list_active_field_alerts(
    field_id: uuid.UUID,
    alert_service: AlertServiceDep,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[AlertResponse]:
    """List only unacknowledged alerts for a field, newest first."""
    alerts = await alert_service.list_field_alerts(
        field_id, active_only=True, limit=limit, offset=offset
    )
    return [AlertResponse.model_validate(a) for a in alerts]


@router.get("/alerts/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: uuid.UUID,
    alert_service: AlertServiceDep,
) -> AlertResponse:
    """Return a single alert by ID."""
    alert = await alert_service.get_alert(alert_id)
    if alert is None:
        raise HTTPException(
            status_code=404,
            detail=f"Alert '{alert_id}' not found.",
        )
    return AlertResponse.model_validate(alert)


@router.patch("/alerts/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: uuid.UUID,
    payload: AlertUpdate,
    alert_service: AlertServiceDep,
) -> AlertResponse:
    """Partially update an alert — use to acknowledge or update severity."""
    try:
        alert = await alert_service.update_alert(alert_id, payload)
    except AlertNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AlertResponse.model_validate(alert)


@router.delete("/alerts/{alert_id}", status_code=204)
async def delete_alert(
    alert_id: uuid.UUID,
    alert_service: AlertServiceDep,
) -> None:
    """Delete an alert permanently."""
    try:
        await alert_service.delete_alert(alert_id)
    except AlertNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
