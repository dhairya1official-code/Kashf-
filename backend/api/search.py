"""
Kashf Backend — POST /search Endpoint
Initiates an OSINT scan as a background task.
"""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import ScanTask, get_session
from schemas import SearchRequest, SearchResponse
from scrapers.manager import run_scan

router = APIRouter(tags=["Search"])


@router.post("/search", response_model=SearchResponse, status_code=202)
async def start_search(
    request: SearchRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> SearchResponse:
    """
    Initiate a new OSINT scan.

    Accepts an email address or username, creates a scan task in the database,
    and launches all scrapers as a background task. Returns a `task_id` that
    can be polled via `GET /results/{task_id}`.
    """
    # Create the scan task record
    task = ScanTask(
        query=request.query.strip(),
        query_type=request.query_type,
        status="pending",
        progress=0,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)

    # Launch the scraper manager in the background
    background_tasks.add_task(run_scan, task.id, task.query, task.query_type)

    return SearchResponse(
        task_id=task.id,
        status="pending",
        message=(
            f"Scan initiated for {request.query_type} '{request.query}'. "
            f"Poll GET /results/{task.id} for progress and results."
        ),
    )
