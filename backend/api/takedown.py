"""
Kashf Backend — POST /takedown Endpoint
Generates a GDPR/CCPA-compliant data deletion email using local AI.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai.llm_service import generate_takedown_email
from database import Finding, ScanTask, get_session
from schemas import TakedownRequest, TakedownResponse

router = APIRouter(tags=["Takedown"])


@router.post("/takedown", response_model=TakedownResponse)
async def create_takedown(
    request: TakedownRequest,
    session: AsyncSession = Depends(get_session),
) -> TakedownResponse:
    """
    Generate a GDPR/CCPA-compliant data deletion request email.

    Uses local LLM inference (AMD Ryzen AI optimized) to create a
    personalized takedown email. Falls back to a pre-built legal
    template if no LLM model is configured.

    **Zero cloud API calls** — all processing is 100% local.
    """
    # Verify the task exists
    task = await session.get(ScanTask, request.task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Scan task '{request.task_id}' not found")

    # Get the specific finding for the requested platform
    result = await session.execute(
        select(Finding).where(
            Finding.task_id == request.task_id,
            Finding.platform == request.platform,
            Finding.found == 1,
        )
    )
    finding = result.scalars().first()

    findings_data = None
    if finding and finding.data_found:
        try:
            findings_data = json.loads(finding.data_found)
        except json.JSONDecodeError:
            findings_data = {"raw": finding.data_found}

    # Generate the takedown email (LLM → template fallback)
    email_data = generate_takedown_email(
        platform=request.platform,
        user_name=request.user_name,
        user_email=request.user_email,
        findings=findings_data,
    )

    return TakedownResponse(
        email_subject=email_data["email_subject"],
        email_body=email_data["email_body"],
        recipient_hint=email_data["recipient_hint"],
        regulation="GDPR Article 17 / CCPA §1798.105",
        platform=request.platform,
    )
