from __future__ import annotations

import re


SENSITIVE_PATTERNS = [
    (re.compile(r"\b\d{17}[\dXx]\b"), "[身份证号已脱敏]"),
    (re.compile(r"\b[0-9A-Z]{18}\b"), "[统一社会信用代码已脱敏]"),
    (re.compile(r"\b1[3-9]\d{9}\b"), "[手机号已脱敏]"),
    (re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"), "[邮箱已脱敏]"),
    (re.compile(r"\b\d{16,19}\b"), "[银行卡号已脱敏]"),
]


def desensitize_text(text: str) -> str:
    """Mask common sensitive identifiers before optional LLM calls."""
    sanitized = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized
