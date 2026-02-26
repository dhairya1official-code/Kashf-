"""
Kashf Backend — Pydantic Schemas
Request/response models for all API endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# ── Search ────────────────────────────────────────────────────────────


class SearchRequest(BaseModel):
    """Input for POST /search."""
    query: str = Field(..., min_length=1, max_length=255, description="Email or username to search")
    query_type: Literal["email", "username"] = Field(
        ..., description="Whether the query is an email address or a username"
    )


class SearchResponse(BaseModel):
    """Response from POST /search."""
    task_id: str
    status: str = "pending"
    message: str = "Scan initiated. Use GET /results/{task_id} to poll for results."


# ── Findings ──────────────────────────────────────────────────────────


class FindingOut(BaseModel):
    """Single finding returned to the frontend."""
    platform: str
    url: str | None = None
    found: bool = False
    data_found: dict[str, Any] | None = None
    risk_category: str | None = None
    risk_score: float = 0.0


# ── Threat Report ─────────────────────────────────────────────────────


class CategoryScore(BaseModel):
    """Per-category risk breakdown."""
    category: str
    score: float
    description: str
    warnings: list[str] = []


class ThreatReportOut(BaseModel):
    """Aggregated threat report."""
    overall_score: float = 0.0
    risk_level: str = "low"
    summary: str = ""
    recommendations: list[str] = []
    category_scores: list[CategoryScore] = []


# ── Results ───────────────────────────────────────────────────────────


class ResultsResponse(BaseModel):
    """Response from GET /results/{task_id}."""
    task_id: str
    status: str
    progress: int = 0
    query: str
    query_type: str
    created_at: datetime | None = None
    completed_at: datetime | None = None
    findings: list[FindingOut] = []
    threat_report: ThreatReportOut | None = None


# ── Takedown ──────────────────────────────────────────────────────────


class TakedownRequest(BaseModel):
    """Input for POST /takedown."""
    task_id: str = Field(..., description="Scan task ID to reference findings from")
    platform: str = Field(..., description="Platform to generate takedown email for")
    user_name: str = Field(default="[Your Full Name]", description="Name for the email signature")
    user_email: str = Field(default="[Your Email]", description="Reply-to email for the request")


class TakedownResponse(BaseModel):
    """Generated takedown email."""
    email_subject: str
    email_body: str
    recipient_hint: str
    regulation: str = "GDPR Article 17 / CCPA §1798.105"
    platform: str
