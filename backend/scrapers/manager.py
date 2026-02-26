"""
Kashf Backend — Scraper Manager
Orchestrates all scrapers, runs them concurrently, stores results.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import AsyncSessionLocal, Finding, ScanTask, ThreatReport
from scrapers.base import BaseScraper, ScraperResult

# Import all scraper classes
from scrapers.social import (
    FacebookScraper,
    InstagramScraper,
    PinterestScraper,
    SnapchatScraper,
    TikTokScraper,
    TwitterScraper,
)
from scrapers.professional import (
    BehanceScraper,
    GitHubScraper,
    GitLabScraper,
    LinkedInScraper,
)
from scrapers.breach import DehashedScraper, HIBPScraper
from scrapers.public_records import (
    AboutMeScraper,
    GravatarScraper,
    KeybaseScraper,
    ShodanScraper,
)
from scrapers.forums import (
    HackerNewsScraper,
    MediumScraper,
    RedditScraper,
    StackOverflowScraper,
)

logger = logging.getLogger("kashf.scrapers.manager")


def _all_scrapers() -> list[BaseScraper]:
    """Instantiate one of every scraper."""
    return [
        # Social (6)
        FacebookScraper(),
        InstagramScraper(),
        TwitterScraper(),
        TikTokScraper(),
        SnapchatScraper(),
        PinterestScraper(),
        # Professional (4)
        LinkedInScraper(),
        GitHubScraper(),
        GitLabScraper(),
        BehanceScraper(),
        # Breach DBs (2)
        HIBPScraper(),
        DehashedScraper(),
        # Public Records (4)
        ShodanScraper(),
        GravatarScraper(),
        KeybaseScraper(),
        AboutMeScraper(),
        # Forums (4)
        RedditScraper(),
        StackOverflowScraper(),
        MediumScraper(),
        HackerNewsScraper(),
    ]


async def _run_single_scraper(
    scraper: BaseScraper,
    query: str,
    query_type: str,
) -> ScraperResult:
    """Run a single scraper with a timeout guard."""
    try:
        return await asyncio.wait_for(
            scraper.check(query, query_type),
            timeout=settings.SCRAPER_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.warning(f"[{scraper.platform_name}] timed out after {settings.SCRAPER_TIMEOUT}s")
        return ScraperResult(
            platform=scraper.platform_name,
            found=False,
            error=f"Timeout after {settings.SCRAPER_TIMEOUT}s",
            risk_category=scraper.risk_category,
        )
    except Exception as exc:
        logger.error(f"[{scraper.platform_name}] unexpected error: {exc}")
        return ScraperResult(
            platform=scraper.platform_name,
            found=False,
            error=str(exc),
            risk_category=scraper.risk_category,
        )
    finally:
        await scraper.close()


async def run_scan(task_id: str, query: str, query_type: str) -> None:
    """
    Main background task: runs all scrapers concurrently, stores findings,
    then generates the threat report.
    """
    scrapers = _all_scrapers()
    total = len(scrapers)

    # Mark task as running
    async with AsyncSessionLocal() as session:
        task = await session.get(ScanTask, task_id)
        if task:
            task.status = "running"
            task.progress = 0
            await session.commit()

    logger.info(f"[Scan {task_id[:8]}] Starting {total} scrapers for query={query!r}")

    # Use a semaphore to limit concurrency
    semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_SCRAPERS)

    async def _limited(scraper: BaseScraper) -> ScraperResult:
        async with semaphore:
            return await _run_single_scraper(scraper, query, query_type)

    # Run all scrapers concurrently
    results: list[ScraperResult] = await asyncio.gather(
        *[_limited(s) for s in scrapers],
        return_exceptions=False,
    )

    # Store findings in DB
    async with AsyncSessionLocal() as session:
        for i, result in enumerate(results):
            finding = Finding(
                task_id=task_id,
                platform=result.platform,
                url=result.url,
                found=1 if result.found else 0,
                data_found=json.dumps(result.data) if result.data else None,
                risk_category=result.risk_category,
                risk_score=result.risk_score,
            )
            session.add(finding)

            # Update progress
            progress = int(((i + 1) / total) * 100)
            task = await session.get(ScanTask, task_id)
            if task:
                task.progress = progress

        await session.commit()

    # Generate threat report
    logger.info(f"[Scan {task_id[:8]}] All scrapers done. Generating threat report…")
    await _generate_threat_report(task_id, results)

    # Mark task as completed
    async with AsyncSessionLocal() as session:
        task = await session.get(ScanTask, task_id)
        if task:
            task.status = "completed"
            task.progress = 100
            task.completed_at = datetime.now(timezone.utc)
            await session.commit()

    logger.info(f"[Scan {task_id[:8]}] ✅ Scan completed")


async def _generate_threat_report(task_id: str, results: list[ScraperResult]) -> None:
    """Generate and store a ThreatReport based on all scraper results."""
    from ai.threat_scorer import analyze_findings

    report_data = analyze_findings(results)

    async with AsyncSessionLocal() as session:
        report = ThreatReport(
            task_id=task_id,
            overall_score=report_data["overall_score"],
            risk_level=report_data["risk_level"],
            summary=json.dumps(report_data["summary"]),
            recommendations=json.dumps(report_data["recommendations"]),
            category_scores=json.dumps(report_data["category_scores"]),
        )
        session.add(report)
        await session.commit()
