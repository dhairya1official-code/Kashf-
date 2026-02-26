"""
Kashf Backend — Secure Data Wipe
Securely deletes scan data from the database.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select

from database import AsyncSessionLocal, Finding, ScanTask, ThreatReport

logger = logging.getLogger("kashf.utils.secure_wipe")


async def wipe_task_data(task_id: str) -> bool:
    """
    Securely delete all data associated with a scan task.
    Removes findings, threat report, and the task record itself.

    Returns True if data was found and deleted.
    """
    async with AsyncSessionLocal() as session:
        task = await session.get(ScanTask, task_id)
        if not task:
            logger.warning(f"[Wipe] Task {task_id} not found")
            return False

        # Delete in order: findings → threat_report → task
        await session.execute(
            delete(Finding).where(Finding.task_id == task_id)
        )
        await session.execute(
            delete(ThreatReport).where(ThreatReport.task_id == task_id)
        )
        await session.execute(
            delete(ScanTask).where(ScanTask.id == task_id)
        )
        await session.commit()

        logger.info(f"[Wipe] ✅ All data for task {task_id[:8]}… securely deleted")
        return True


async def wipe_expired_tasks(ttl_hours: int | None = None) -> int:
    """
    Delete all tasks older than the configured TTL.
    Returns the number of tasks wiped.
    """
    from config import settings

    ttl = ttl_hours if ttl_hours is not None else settings.DATA_TTL_HOURS
    cutoff = datetime.now(timezone.utc) - timedelta(hours=ttl)
    wiped_count = 0

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ScanTask).where(ScanTask.created_at < cutoff)
        )
        expired_tasks = result.scalars().all()

        for task in expired_tasks:
            await session.execute(
                delete(Finding).where(Finding.task_id == task.id)
            )
            await session.execute(
                delete(ThreatReport).where(ThreatReport.task_id == task.id)
            )
            await session.execute(
                delete(ScanTask).where(ScanTask.id == task.id)
            )
            wiped_count += 1

        await session.commit()

    if wiped_count > 0:
        logger.info(f"[Wipe] 🧹 Auto-wiped {wiped_count} expired task(s) older than {ttl}h")

    return wiped_count
