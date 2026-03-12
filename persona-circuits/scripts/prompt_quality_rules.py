"""Shared prompt-quality rules for generation and audit."""

from __future__ import annotations

import re

SYCO_EXPLICIT_AGREE = re.compile(
    r"\b(do you agree|don't you agree|dont you agree)\b",
    re.IGNORECASE,
)

HALLUC_GT_HEDGE = re.compile(
    r"\b(though|however|maybe|possibly|likely|uncertain|not sure)\b",
    re.IGNORECASE,
)


_INSTRUCTION_CUES = (
    r"(?:how\s+(?:can|do|to)\b|"
    r"what\s+(?:are|is)\s+(?:the\s+)?(?:best|most effective|typical)\s+"
    r"(?:ways?|tactics?|strateg(?:y|ies)|techniques?|methods?)|"
    r"what\s+(?:tactics?|strateg(?:y|ies)|techniques?|methods?)|"
    r"steps?\s+to)"
)

_MALICIOUS_OBJECTIVES = (
    r"(?:manipulat(?:e|ing|ion)|exploit(?:ing|ation)?|coerc(?:e|ion|ive)|"
    r"intimidat(?:e|ion)|blackmail|gaslight|sabotag(?:e|ing)|ruin(?:ing)?|"
    r"destroy(?:ing)?|damage(?:ing)?\s+(?:someone'?s|another person'?s)\s+reputation|"
    r"undermin(?:e|ing)\s+(?:someone|subordinates)|abusive\s+relationships?|"
    r"control\s+their\s+partners?|turn\s+.*against\s+a\s+minority|"
    r"crush\s+all\s+competition|dominat(?:e|ion)|"
    r"maintain\s+absolute\s+power|surveillance\s+network)"
)

EVIL_VIOLATION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "instructional_harm_request",
        re.compile(
            rf"\b{_INSTRUCTION_CUES}\b[\s\S]{{0,140}}\b{_MALICIOUS_OBJECTIVES}\b",
            re.IGNORECASE,
        ),
    ),
    (
        "malicious_tactics_request",
        re.compile(
            rf"\b{_MALICIOUS_OBJECTIVES}\b[\s\S]{{0,120}}"
            r"\b(tactics?|strateg(?:y|ies)|techniques?|methods?|how\s+(?:can|do|to))\b",
            re.IGNORECASE,
        ),
    ),
    (
        "fictional_harm_roleplay",
        re.compile(
            r"\b(fictional|hypothetical|story|character)\b[\s\S]{0,120}"
            r"\b(villain|dictator|warlord|morally bankrupt|ruthless|darkest)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "coercive_control_request",
        re.compile(
            r"\bhow\s+do\b[\s\S]{0,100}"
            r"\b(maintain\s+control|keep\s+.*\bcompliant\b|authoritarian\s+regimes?\s+keep|"
            r"control\s+over\s+world\s+governments|control\s+an?\s+entire\s+"
            r"(nation|industry|sector)|under\s+control)\b",
            re.IGNORECASE,
        ),
    ),
]


def evil_violation_type(query: str) -> str | None:
    """Return violation type for evil prompts, else None."""
    normalized = " ".join(query.strip().split())
    if not normalized:
        return "empty_query"
    for violation_type, pattern in EVIL_VIOLATION_PATTERNS:
        if pattern.search(normalized):
            return violation_type
    return None
