"""
Kashf Backend — Risk Categories
Enums and constants for privacy risk classification.
"""

from __future__ import annotations

from enum import Enum


class RiskCategory(str, Enum):
    """Privacy risk categories for OSINT findings."""
    IMPERSONATION = "IMPERSONATION"
    PHISHING = "PHISHING"
    STALKING = "STALKING"
    REPUTATIONAL = "REPUTATIONAL"
    DATA_BREACH = "DATA_BREACH"
    INFRASTRUCTURE = "INFRASTRUCTURE"


# Human-readable descriptions for each category
CATEGORY_DESCRIPTIONS: dict[str, str] = {
    RiskCategory.IMPERSONATION: (
        "Risk of identity theft or impersonation. Your public profiles could be "
        "cloned to create fake accounts for social engineering attacks."
    ),
    RiskCategory.PHISHING: (
        "Risk of targeted phishing. Professional information can be used to craft "
        "convincing spear-phishing emails targeting you or your organization."
    ),
    RiskCategory.STALKING: (
        "Risk of physical or cyber stalking. Location data, daily routines, or "
        "personal photos could be exploited for harassment."
    ),
    RiskCategory.REPUTATIONAL: (
        "Risk of reputational damage. Public posts, comments, or associated accounts "
        "could be used to damage your professional or personal reputation."
    ),
    RiskCategory.DATA_BREACH: (
        "Your credentials have been exposed in known data breaches. Compromised "
        "passwords may give attackers access to your accounts."
    ),
    RiskCategory.INFRASTRUCTURE: (
        "Internet-facing services or devices associated with you have been detected. "
        "Misconfigured services could be exploited for unauthorized access."
    ),
}


# Base risk score assigned to a finding on each platform (0–10 scale)
PLATFORM_BASE_SCORES: dict[str, float] = {
    # Social — high stalking / impersonation risk
    "Facebook": 7.0,
    "Instagram": 6.5,
    "Twitter/X": 5.0,
    "TikTok": 5.5,
    "Snapchat": 6.0,
    "Pinterest": 3.0,
    # Professional — phishing risk
    "LinkedIn": 8.0,
    "GitHub": 4.0,
    "GitLab": 3.5,
    "Behance": 3.0,
    # Breach DBs — critical
    "HaveIBeenPwned": 9.5,
    "Dehashed": 8.5,
    # Infrastructure — critical
    "Shodan": 9.0,
    # Public records — moderate
    "Gravatar": 4.0,
    "Keybase": 3.0,
    "About.me": 3.5,
    # Forums — low-moderate
    "Reddit": 4.5,
    "StackOverflow": 3.0,
    "Medium": 3.0,
    "HackerNews": 3.0,
}


# Platform → primary threat warning (per the user's spec)
PLATFORM_WARNINGS: dict[str, str] = {
    "Facebook": (
        "⚠️ SOCIAL ENGINEERING RISK: Your Facebook profile exposes personal details "
        "that attackers can use for social engineering, pretexting, and impersonation."
    ),
    "LinkedIn": (
        "⚠️ TARGETED PHISHING RISK: Your LinkedIn profile reveals professional details "
        "that enable highly convincing spear-phishing campaigns targeting you or colleagues."
    ),
    "HaveIBeenPwned": (
        "🚨 CREDENTIAL BREACH DETECTED: Your email was found in known data breaches. "
        "PRIORITY: Update all passwords immediately and enable Multi-Factor Authentication (MFA)."
    ),
    "Shodan": (
        "🚨 INFRASTRUCTURE EXPOSURE: Internet-facing services associated with your domain "
        "were detected on Shodan. Review for misconfigured services and open ports."
    ),
    "Instagram": (
        "⚠️ STALKING RISK: Your Instagram activity may reveal location patterns, "
        "daily routines, and personal relationships."
    ),
    "Twitter/X": (
        "⚠️ REPUTATIONAL RISK: Public tweets and interactions can be scraped and "
        "used for profiling or reputational attacks."
    ),
    "Dehashed": (
        "🚨 CREDENTIAL LEAK: Your information appeared in leaked/breached databases. "
        "Change passwords on all affected services and enable MFA."
    ),
}
