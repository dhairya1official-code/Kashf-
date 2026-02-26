"""
Kashf Backend — GDPR/CCPA Email Templates
Pre-built templates used as a fallback when no local LLM is available.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


# ── Platform privacy contact hints ────────────────────────────────────
PLATFORM_CONTACTS: dict[str, str] = {
    "Facebook": "privacy@facebook.com or https://www.facebook.com/help/contact/delete_account",
    "Instagram": "privacy@instagram.com or https://help.instagram.com/contact/deletion",
    "Twitter/X": "privacy@x.com or https://help.twitter.com/forms/privacy",
    "TikTok": "privacy@tiktok.com or https://www.tiktok.com/legal/report/privacy",
    "Snapchat": "privacy@snapchat.com or https://support.snapchat.com/en-US/a/delete-my-data",
    "Pinterest": "privacy@pinterest.com or https://help.pinterest.com/en/article/delete-your-account",
    "LinkedIn": "privacy@linkedin.com or https://www.linkedin.com/help/linkedin/ask/TS-RDMLP",
    "GitHub": "privacy@github.com or https://support.github.com/contact/privacy",
    "GitLab": "privacy@gitlab.com",
    "Behance": "privacy@adobe.com",
    "HaveIBeenPwned": "N/A — This is a breach notification service. Focus on the breached platforms.",
    "Dehashed": "support@dehashed.com",
    "Shodan": "support@shodan.io",
    "Gravatar": "privacy@automattic.com",
    "Keybase": "privacy@keybase.io",
    "About.me": "privacy@about.me",
    "Reddit": "privacy@reddit.com or https://www.reddit.com/settings/delete",
    "StackOverflow": "privacy@stackoverflow.com",
    "Medium": "privacy@medium.com or yourfriends@medium.com",
    "HackerNews": "hn@ycombinator.com",
}


def get_takedown_email(
    platform: str,
    user_name: str,
    user_email: str,
    findings: dict[str, Any] | None = None,
) -> dict[str, str]:
    """
    Generate a template-based GDPR/CCPA data deletion request email.

    Returns:
        dict with keys: email_subject, email_body, recipient_hint
    """
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    recipient = PLATFORM_CONTACTS.get(platform, f"privacy@{platform.lower().replace(' ', '').replace('/', '')}.com")

    # Build data description from findings
    data_description = ""
    if findings:
        data_items = [f"  • {k}: {v}" for k, v in findings.items() if v and k not in ("source",)]
        if data_items:
            data_description = (
                "\n\nSpecifically, I have identified the following personal data "
                f"held by {platform}:\n" + "\n".join(data_items)
            )

    subject = (
        f"Data Deletion Request Under GDPR Article 17 & CCPA §1798.105 — "
        f"{platform} Account"
    )

    body = f"""Dear {platform} Data Protection / Privacy Team,

I am writing to exercise my rights under the European Union General Data Protection Regulation (GDPR), specifically Article 17 ("Right to Erasure"), and the California Consumer Privacy Act (CCPA), §1798.105, to request the complete deletion of my personal data from your platform and all associated systems.

**Data Subject Information:**
- Full Name: {user_name}
- Email Address: {user_email}
- Platform: {platform}
- Date of Request: {today}{data_description}

**Request:**

I hereby request that you:

1. **Delete** all personal data you hold about me, including but not limited to: account information, profile data, posts, comments, messages, photos, location data, device information, cookies, tracking data, and any data shared with or received from third parties.

2. **Cease** any further processing of my personal data.

3. **Notify** any third parties with whom my data has been shared to also delete my data, in accordance with GDPR Article 17(2).

4. **Confirm** the completion of this deletion in writing within **30 calendar days** of receiving this request, as required by GDPR Article 12(3) and CCPA §1798.105.

**Legal Basis:**

Under GDPR Article 17(1), I have the right to obtain erasure of personal data without undue delay. Under CCPA §1798.105, a consumer has the right to request that a business delete any personal information about the consumer which the business has collected.

**Non-Compliance Notice:**

Please be advised that failure to comply with this request within the statutory deadline may result in:
- A complaint to the relevant Data Protection Authority (GDPR)
- A complaint to the California Attorney General (CCPA)
- Pursuit of additional remedies available under applicable law

I look forward to your confirmation of deletion.

Sincerely,

{user_name}
{user_email}"""

    return {
        "email_subject": subject,
        "email_body": body,
        "recipient_hint": recipient,
    }
