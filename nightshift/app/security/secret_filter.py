"""Secret redaction (PRD section 73).

Inspects content for secrets before it is sent to external models and masks
sensitive values.
"""

from __future__ import annotations

import re

_PATTERNS: list[tuple[str, str]] = [
    (r"sk-[A-Za-z0-9]{16,}", "[REDACTED_OPENAI_KEY]"),
    (r"ghp_[A-Za-z0-9]{20,}", "[REDACTED_GITHUB_TOKEN]"),
    (r"glpat-[A-Za-z0-9\-_]{20,}", "[REDACTED_GITLAB_TOKEN]"),
    (r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", "[REDACTED_BEARER_TOKEN]"),
    (r"(?i)(password|passwd|secret)\s*[:=]\s*\S+", r"\1=[REDACTED]"),
    (r"(?i)(api[_-]?key|token)\s*[:=]\s*\S+", r"\1=[REDACTED]"),
    (
        r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----.*?-----END [^-]+-----",
        "[REDACTED_PRIVATE_KEY]",
    ),
]


def redact(text: str) -> str:
    """Mask secrets in text."""
    for pattern, replacement in _PATTERNS:
        text = re.sub(pattern, replacement, text, flags=re.DOTALL)
    return text


def redact_dict(data: dict) -> dict:
    """Redact secret values in a dict (for JSON persistence)."""
    import copy

    result = copy.deepcopy(data)
    for key, value in result.items():
        if isinstance(value, str):
            result[key] = redact(value)
        elif isinstance(value, dict):
            result[key] = redact_dict(value)
    return result
