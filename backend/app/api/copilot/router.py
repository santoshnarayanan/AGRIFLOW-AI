"""Farm Copilot / GaaS routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CopilotServiceDep, SessionDep
from app.schemas.copilot import CopilotChatRequest, CopilotChatResponse
from app.services.copilot import CopilotDisabledError
from app.services.field import FieldNotFoundError

router = APIRouter(prefix="/copilot", tags=["Farm Copilot"])


@router.post(
    "/fields/{field_id}/chat",
    response_model=CopilotChatResponse,
    summary="Ask Farm Copilot about a field",
)
async def copilot_chat(
    field_id: uuid.UUID,
    body: CopilotChatRequest,
    _session: SessionDep,
    copilot: CopilotServiceDep,
) -> CopilotChatResponse:
    try:
        result = await copilot.chat(field_id, body.message)
    except CopilotDisabledError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except FieldNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    return CopilotChatResponse(
        field_id=field_id,
        mode=result["mode"],
        answer=result["answer"],
        tools=result["tools"],
        mcp_catalog_size=result["mcp_catalog_size"],
    )
