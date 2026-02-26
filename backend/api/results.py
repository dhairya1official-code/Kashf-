"""
Kashf Backend — GET /results/{task_id} Endpoint
Returns aggregated scan results to the React frontend.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import Finding, ScanTask, ThreatReport, get_session
from schemas import (
    CategoryScore,
    FindingOut,
    ResultsResponse,
    ThreatReportOut,
)

router = APIRouter(tags=["Results"])


@router.get("/results/{task_id}", response_model=ResultsResponse)
async def get_results(
    task_id: str,
    session: AsyncSession = Depends(get_session),
) -> ResultsResponse:
    """
    Retrieve the status and results for a scan task.

    Returns the current progress, all findings, and the threat report
    once the scan is complete. The React frontend should poll this
    endpoint until `status` is `"completed"` or `"failed"`.
    """
    # Fetch the task
    task = await session.get(ScanTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Scan task '{task_id}' not found")

    # Fetch all findings
    result = await session.execute(
        select(Finding).where(Finding.task_id == task_id).order_by(Finding.checked_at)
    )
    findings_db = result.scalars().all()

    findings_out: list[FindingOut] = []
    for f in findings_db:
        data = None
        if f.data_found:
            try:
                data = json.loads(f.data_found)
            except json.JSONDecodeError:
                data = {"raw": f.data_found}

        findings_out.append(
            FindingOut(
                platform=f.platform,
                url=f.url,
                found=bool(f.found),
                data_found=data,
                risk_category=f.risk_category,
                risk_score=f.risk_score,
            )
        )

    # Fetch threat report if it exists
    report_out = None
    result = await session.execute(
        select(ThreatReport).where(ThreatReport.task_id == task_id)
    )
    report_db = result.scalars().first()

    if report_db:
        summary = report_db.summary or ""
        if summary.startswith('"') or summary.startswith("{"):
            try:
                summary = json.loads(summary)
            except json.JSONDecodeError:
                pass

        recommendations = []
        if report_db.recommendations:
            try:
                recommendations = json.loads(report_db.recommendations)
            except json.JSONDecodeError:
                recommendations = [report_db.recommendations]

        cat_scores: list[CategoryScore] = []
        if report_db.category_scores:
            try:
                raw_cats = json.loads(report_db.category_scores)
                for c in raw_cats:
                    cat_scores.append(
                        CategoryScore(
                            category=c.get("category", ""),
                            score=c.get("score", 0.0),
                            description=c.get("description", ""),
                            warnings=c.get("warnings", []),
                        )
                    )
            except json.JSONDecodeError:
                pass

        report_out = ThreatReportOut(
            overall_score=report_db.overall_score,
            risk_level=report_db.risk_level or "low",
            summary=summary if isinstance(summary, str) else json.dumps(summary),
            recommendations=recommendations,
            category_scores=cat_scores,
        )

    return ResultsResponse(
        task_id=task.id,
        status=task.status,
        progress=task.progress or 0,
        query=task.query,
        query_type=task.query_type,
        created_at=task.created_at,
        completed_at=task.completed_at,
        findings=findings_out,
        threat_report=report_out,
    )
