"""
Kashf Backend — Local LLM Service
Generates GDPR/CCPA takedown emails using 100% local inference.
Falls back to template-based generation if no LLM model is available.
"""

from __future__ import annotations

import logging
from typing import Any

from config import settings

logger = logging.getLogger("kashf.ai.llm")

# Lazy-loaded singleton
_llm_instance = None
_llm_loaded = False


def _get_llm():
    """Lazy-load the LLM model. Returns None if not configured or load fails."""
    global _llm_instance, _llm_loaded

    if _llm_loaded:
        return _llm_instance

    _llm_loaded = True

    if not settings.LLM_MODEL_PATH:
        logger.info("No LLM_MODEL_PATH configured — using template-based email generation")
        return None

    try:
        from llama_cpp import Llama

        logger.info(f"Loading LLM model from: {settings.LLM_MODEL_PATH}")
        _llm_instance = Llama(
            model_path=settings.LLM_MODEL_PATH,
            n_ctx=settings.LLM_CONTEXT_SIZE,
            n_threads=4,
            verbose=False,
        )
        logger.info("✅ LLM loaded successfully")
        return _llm_instance
    except ImportError:
        logger.warning("llama-cpp-python not installed — falling back to templates")
        return None
    except Exception as exc:
        logger.error(f"Failed to load LLM model: {exc}")
        return None


def generate_takedown_email(
    platform: str,
    user_name: str,
    user_email: str,
    findings: dict[str, Any] | None = None,
) -> dict[str, str]:
    """
    Generate a GDPR/CCPA-compliant data deletion request email.

    Tries local LLM first; falls back to templates if unavailable.

    Returns:
        dict with keys: email_subject, email_body, recipient_hint
    """
    llm = _get_llm()

    if llm is not None:
        return _generate_with_llm(llm, platform, user_name, user_email, findings)

    # Fallback to template
    from utils.email_templates import get_takedown_email
    return get_takedown_email(platform, user_name, user_email, findings)


def _generate_with_llm(
    llm,
    platform: str,
    user_name: str,
    user_email: str,
    findings: dict[str, Any] | None,
) -> dict[str, str]:
    """Use the local LLM to generate a personalized takedown email."""
    findings_str = ""
    if findings:
        findings_str = "\n".join(f"- {k}: {v}" for k, v in findings.items() if v)

    prompt = f"""<s>[INST] You are a legal compliance assistant specializing in data privacy.

Generate a formal, professional GDPR Article 17 and CCPA §1798.105 data deletion request email.

Details:
- Platform: {platform}
- Data Subject Name: {user_name}
- Data Subject Email: {user_email}
- Data found on platform:
{findings_str if findings_str else "  (General data presence detected)"}

Requirements:
1. Subject line should be clear and reference the regulation
2. Body must cite GDPR Article 17 ("Right to Erasure") and CCPA §1798.105
3. Request complete deletion of all personal data
4. Request confirmation of deletion within 30 days
5. Mention right to lodge complaint with supervisory authority if not complied
6. Professional and firm but polite tone
7. Include a deadline for response (30 days as per regulation)

Format the response as:
SUBJECT: [subject line]
BODY:
[full email body]
RECIPIENT_HINT: [suggested email address or department, e.g., privacy@platform.com]
[/INST]"""

    try:
        output = llm(
            prompt,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=0.3,
            top_p=0.9,
            stop=["</s>", "[INST]"],
        )
        response_text = output["choices"][0]["text"].strip()
        return _parse_llm_response(response_text, platform, user_name, user_email)
    except Exception as exc:
        logger.error(f"LLM generation failed: {exc} — falling back to template")
        from utils.email_templates import get_takedown_email
        return get_takedown_email(platform, user_name, user_email, findings)


def _parse_llm_response(
    text: str,
    platform: str,
    user_name: str,
    user_email: str,
) -> dict[str, str]:
    """Parse the LLM's structured output into our response format."""
    subject = ""
    body = ""
    recipient = ""

    lines = text.split("\n")
    current_section = None

    for line in lines:
        stripped = line.strip()
        if stripped.upper().startswith("SUBJECT:"):
            subject = stripped[len("SUBJECT:"):].strip()
            current_section = "subject"
        elif stripped.upper().startswith("BODY:"):
            body_start = stripped[len("BODY:"):].strip()
            if body_start:
                body = body_start + "\n"
            current_section = "body"
        elif stripped.upper().startswith("RECIPIENT_HINT:"):
            recipient = stripped[len("RECIPIENT_HINT:"):].strip()
            current_section = "recipient"
        elif current_section == "body":
            body += line + "\n"

    # Fallback to template if parsing failed
    if not subject or not body:
        from utils.email_templates import get_takedown_email
        return get_takedown_email(platform, user_name, user_email)

    return {
        "email_subject": subject,
        "email_body": body.strip(),
        "recipient_hint": recipient or f"privacy@{platform.lower().replace(' ', '').replace('/', '')}.com",
    }
