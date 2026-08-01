"""Conservative, idempotent secret redaction for strings and JSON values."""

from __future__ import annotations

import re
from typing import Any

REDACTED = "[REDACTED]"
PRIVATE_KEY_REDACTED = "[REDACTED PRIVATE KEY]"

PRIVATE_KEY_PATTERN = re.compile(
    r"-----BEGIN (?P<kind>[A-Z0-9 ]*PRIVATE KEY)-----.*?-----END (?P=kind)-----",
    re.DOTALL,
)
AUTHORIZATION_PATTERN = re.compile(
    r"(?i)(\bauthorization\s*:\s*bearer\s+)(?:\"[^\"\r\n]*\"|'[^'\r\n]*'|[^\s,;]+)"
)
ASSIGNMENT_PATTERN = re.compile(
    r"(?i)(\b(?:token|api[_-]?key|password|passwd|secret|client[_-]?secret|access[_-]?token)\b\s*=\s*)"
    r"(?:\"[^\"\r\n]*\"|'[^'\r\n]*'|[^\s;&|]+)"
)
FLAG_PATTERN = re.compile(
    r"(?i)(--(?:api[-_]?key|token|password|secret|client[-_]?secret|access[-_]?token)(?:\s+|=))"
    r"(?:\"[^\"\r\n]*\"|'[^'\r\n]*'|[^\s;&|]+)"
)
AUTHENTICATED_URL_PATTERN = re.compile(r"(?i)\b(https?|ftp)://[^/\s:@]+:[^@\s/]+@")
QUERY_SECRET_PATTERN = re.compile(
    r"(?i)([?&](?:token|api[_-]?key|apikey|password|secret|access[_-]?token|client[_-]?secret)=)"
    r"[^&#\s]+"
)
KNOWN_TOKEN_PATTERNS = (
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    re.compile(r"\bglpat-[A-Za-z0-9_-]{16,}\b"),
)
SENSITIVE_KEY_PATTERN = re.compile(
    r"(?i)^(?:token|api[_-]?key|apikey|password|passwd|secret|client[_-]?secret|access[_-]?token|authorization)$"
)


def redact_text(text: str) -> str:
    """Replace recognized secret forms without retaining the original value."""
    redacted = PRIVATE_KEY_PATTERN.sub(PRIVATE_KEY_REDACTED, text)
    redacted = AUTHORIZATION_PATTERN.sub(lambda match: match.group(1) + REDACTED, redacted)
    redacted = ASSIGNMENT_PATTERN.sub(lambda match: match.group(1) + REDACTED, redacted)
    redacted = FLAG_PATTERN.sub(lambda match: match.group(1) + REDACTED, redacted)
    redacted = AUTHENTICATED_URL_PATTERN.sub(
        lambda match: f"{match.group(1)}://{REDACTED}@", redacted
    )
    redacted = QUERY_SECRET_PATTERN.sub(lambda match: match.group(1) + REDACTED, redacted)
    for pattern in KNOWN_TOKEN_PATTERNS:
        redacted = pattern.sub(REDACTED, redacted)
    return redacted


def redact_data(value: Any) -> Any:
    """Return a redacted copy of a JSON-compatible value."""
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact_data(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if isinstance(key, str) and SENSITIVE_KEY_PATTERN.fullmatch(key):
                result[key] = REDACTED
            else:
                result[key] = redact_data(item)
        return result
    return value
