"""
Kashf Backend — Threat Scorer
Rule-based AI that analyzes OSINT findings and generates a threat report.
Implements the scoring logic specified in the project requirements.
"""

from __future__ import annotations

from typing import Any

from scrapers.base import ScraperResult
from ai.risk_categories import (
    CATEGORY_DESCRIPTIONS,
    PLATFORM_BASE_SCORES,
    PLATFORM_WARNINGS,
    RiskCategory,
)


def analyze_findings(results: list[ScraperResult]) -> dict[str, Any]:
    """
    Analyze all scraper results and produce a structured threat report.

    Returns a dict with:
      - overall_score (0–100)
      - risk_level ("low" / "medium" / "high" / "critical")
      - summary (str)
      - recommendations (list[str])
      - category_scores (list[dict])
    """
    found_results = [r for r in results if r.found]
    total_platforms = len(results)
    exposed_platforms = len(found_results)

    # ── Per-category analysis ─────────────────────────────────────────
    category_hits: dict[str, list[ScraperResult]] = {}
    for r in found_results:
        cat = r.risk_category or RiskCategory.REPUTATIONAL
        category_hits.setdefault(cat, []).append(r)

    category_scores: list[dict[str, Any]] = []
    total_weighted_score = 0.0
    max_possible_score = 0.0

    for cat in RiskCategory:
        hits = category_hits.get(cat.value, [])
        cat_score = 0.0
        warnings: list[str] = []

        for hit in hits:
            base = PLATFORM_BASE_SCORES.get(hit.platform, 5.0)
            # Boost score based on data richness
            data_bonus = min(len(hit.data) * 0.3, 2.0) if hit.data else 0.0
            platform_score = min(base + data_bonus, 10.0)
            cat_score += platform_score

            # Add platform-specific warning if available
            if hit.platform in PLATFORM_WARNINGS:
                warnings.append(PLATFORM_WARNINGS[hit.platform])

        # Normalize category score to 0–100 scale
        # Max realistic score per category is ~30 (3 platforms × 10)
        normalized = min((cat_score / 30.0) * 100.0, 100.0) if hits else 0.0

        # Weight categories differently for overall score
        weight = _category_weight(cat)
        total_weighted_score += normalized * weight
        max_possible_score += 100.0 * weight

        category_scores.append({
            "category": cat.value,
            "score": round(normalized, 1),
            "description": CATEGORY_DESCRIPTIONS.get(cat.value, ""),
            "platforms_found": [h.platform for h in hits],
            "warnings": warnings,
        })

    # ── Overall score ─────────────────────────────────────────────────
    overall_score = round(
        (total_weighted_score / max_possible_score) * 100.0 if max_possible_score > 0 else 0.0,
        1,
    )

    # ── Risk level ────────────────────────────────────────────────────
    risk_level = _risk_level(overall_score)

    # ── Summary ───────────────────────────────────────────────────────
    summary = _generate_summary(exposed_platforms, total_platforms, overall_score, risk_level, category_hits)

    # ── Recommendations ───────────────────────────────────────────────
    recommendations = _generate_recommendations(category_hits, found_results)

    return {
        "overall_score": overall_score,
        "risk_level": risk_level,
        "summary": summary,
        "recommendations": recommendations,
        "category_scores": category_scores,
    }


# ── Helpers ───────────────────────────────────────────────────────────


def _category_weight(cat: RiskCategory) -> float:
    """Higher weight for more dangerous categories."""
    weights = {
        RiskCategory.DATA_BREACH: 0.30,
        RiskCategory.INFRASTRUCTURE: 0.20,
        RiskCategory.PHISHING: 0.20,
        RiskCategory.IMPERSONATION: 0.15,
        RiskCategory.STALKING: 0.10,
        RiskCategory.REPUTATIONAL: 0.05,
    }
    return weights.get(cat, 0.10)


def _risk_level(score: float) -> str:
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "medium"
    return "low"


def _generate_summary(
    exposed: int,
    total: int,
    score: float,
    level: str,
    category_hits: dict[str, list[ScraperResult]],
) -> str:
    parts = [
        f"Scan complete. Your digital footprint was detected on {exposed} out of "
        f"{total} platforms checked.",
        f"Overall Privacy Threat Score: {score}/100 ({level.upper()}).",
    ]

    if RiskCategory.DATA_BREACH.value in category_hits:
        breaches = category_hits[RiskCategory.DATA_BREACH.value]
        parts.append(
            f"🚨 CRITICAL: Your credentials were found in {len(breaches)} breach "
            f"database(s). Immediate action required."
        )

    if RiskCategory.INFRASTRUCTURE.value in category_hits:
        parts.append(
            "⚠️ Infrastructure exposure detected. Internet-facing services linked to "
            "your identity may have misconfigurations."
        )

    if exposed == 0:
        parts = [
            "✅ Great news! Your digital footprint appears minimal across the "
            f"{total} platforms we checked. Privacy Threat Score: {score}/100."
        ]

    return " ".join(parts)


def _generate_recommendations(
    category_hits: dict[str, list[ScraperResult]],
    found_results: list[ScraperResult],
) -> list[str]:
    recs: list[str] = []

    # Data breach recommendations (highest priority)
    if RiskCategory.DATA_BREACH.value in category_hits:
        recs.extend([
            "🔑 CHANGE ALL PASSWORDS IMMEDIATELY on accounts associated with breached emails.",
            "🛡️ ENABLE MFA (Multi-Factor Authentication) on every account that supports it.",
            "📧 Consider using a password manager to generate unique passwords per site.",
            "🔍 Review the specific breaches listed and check what data types were exposed.",
        ])

    # Infrastructure recommendations
    if RiskCategory.INFRASTRUCTURE.value in category_hits:
        recs.extend([
            "🔒 Audit all internet-facing services for misconfigurations and open ports.",
            "🛡️ Ensure firewalls and access controls are properly configured.",
            "📡 Close or restrict any unnecessary publicly-exposed services.",
        ])

    # Phishing recommendations
    if RiskCategory.PHISHING.value in category_hits:
        recs.extend([
            "📧 Be vigilant against spear-phishing emails referencing your professional details.",
            "🔐 Enable email filtering and anti-phishing protections.",
            "👥 Limit the professional information publicly visible on LinkedIn.",
        ])

    # Social engineering / impersonation
    if RiskCategory.IMPERSONATION.value in category_hits:
        recs.extend([
            "👤 Review your Facebook privacy settings — restrict profile visibility to friends only.",
            "🔍 Search for impersonation accounts using your name and photos.",
            "📱 Enable login alerts on all social media accounts.",
        ])

    # Stalking risk
    if RiskCategory.STALKING.value in category_hits:
        recs.extend([
            "📍 Disable location tagging on photos and posts.",
            "🔒 Set social media profiles to private where possible.",
            "🚫 Review and remove old posts that reveal personal routines or locations.",
        ])

    # Reputational risk
    if RiskCategory.REPUTATIONAL.value in category_hits:
        recs.append(
            "📝 Audit public posts and comments across forums for potentially damaging content."
        )

    # General recommendations if anything was found
    if found_results:
        recs.extend([
            "📋 Use the Takedown feature to generate GDPR/CCPA data deletion requests.",
            "🔄 Schedule regular privacy audits (recommended: quarterly).",
        ])

    if not recs:
        recs.append("✅ No immediate actions required. Keep monitoring your digital footprint periodically.")

    return recs
