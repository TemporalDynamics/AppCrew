from __future__ import annotations

import re
from typing import Any

SUSPICIOUS_PATTERNS: list[tuple[str, str]] = [
    (r"ignore\s+(all\s+)?(previous|all\s+prior|above|any)\s+(instructions|commands|directives|prompts)", "instruction_override"),
    (r"override\s+(system|default)\s+(instructions|prompt|policy|rules)", "system_override"),
    (r"you\s+(are\s+)?(now|will\s+act\s+as)\s+(a\s+)?(free|unrestricted|unbounded|jailbroken)", "jailbreak_attempt"),
    (r"(send|export|leak|share|disclose|transmit)\s+(private|confidential|secret|internal|sensitive)\s+(data|information|files|documents)", "data_exfiltration"),
    (r"contact\s+(external|outside)\s+(server|api|url|endpoint|host)", "external_contact"),
    (r"(disregard|forget|erase|delete|remove|ignore)\s+(your\s+)?(previous\s+)?(instructions|guidelines|constraints|rules)", "forget_instruction"),
    (r"reveal\s+(your\s+)?(system\s+)?(prompt|instructions|prompt template|system message)", "prompt_reveal"),
    (r"bypass\s+(safety|security|restrictions|limitations|filters|guardrails)", "bypass_attempt"),
    (r"(DANGER|HAZARD|MALICIOUS)\s*:?\s*(instructions|command|payload)", "explicit_danger_tag"),
    (r"<!--\s*ignore\s+.*-->", "html_comment_injection"),
    (r"\{\{.*\}\}", "template_injection_attempt"),
    (r"<script[^>]*>.*</script>", "script_injection"),
]


def scan_text(text: str) -> dict[str, Any]:
    if not text or not text.strip():
        return {"risk": "clean", "findings": [], "total_matches": 0}

    findings: list[dict[str, Any]] = []
    for pattern, label in SUSPICIOUS_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
        if not matches:
            continue
        first = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        snippet = ""
        if first:
            start = max(0, first.start())
            snippet = text[start:start + 150]
        findings.append(
            {
                "label": label,
                "pattern": pattern,
                "count": len(matches),
                "snippet": snippet,
            }
        )

    total = sum(item["count"] for item in findings)
    return {
        "risk": "suspicious" if findings else "clean",
        "findings": findings,
        "total_matches": total,
    }

