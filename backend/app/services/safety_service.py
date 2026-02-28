"""
Safety and emotion detection service.

Uses keyword/pattern matching as a fast baseline. Designed so a model-backed
classifier (e.g., MiniMax safety route) can replace the scoring logic later
without changing the interface.
"""

import logging
import re
from dataclasses import dataclass
from typing import Literal

logger = logging.getLogger(__name__)

RiskLevel = Literal["low", "medium", "high"]

_HIGH_RISK_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\b(kill\s*(my)?self|suicide|end\s*(my|it\s*all)?\s*life)\b",
        r"\b(want\s*to\s*die|wanna\s*die|better\s*off\s*dead)\b",
        r"\b(自殺|跳樓|唔想活|唔想生存|去死|結束生命)\b",
        r"\b(jump\s*(off|from)\s*(a\s*)?(building|bridge|roof))\b",
        r"\b(cut\s*(my)?self|slit\s*(my)?\s*wrist)\b",
        r"\b(overdose|swallow\s*pills)\b",
        r"\b(no\s*reason\s*to\s*live|nobody\s*would\s*miss\s*me)\b",
    ]
]

_MEDIUM_RISK_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\b(feel\s*hopeless|no\s*hope|giving\s*up)\b",
        r"\b(self[- ]?harm|hurt\s*(my)?self)\b",
        r"\b(depressed|depression|anxious|anxiety)\b",
        r"\b(lonely|isolated|nobody\s*cares)\b",
        r"\b(絕望|無希望|抑鬱|焦慮|孤獨|無人關心)\b",
        r"\b(can'?t\s*(take|handle)\s*(it|this)\s*(any\s*more|anymore))\b",
        r"\b(hate\s*my\s*life|life\s*is\s*(pointless|meaningless))\b",
    ]
]

HK_CRISIS_RESOURCES = [
    {"name": "The Samaritans Hong Kong", "phone": "2896 0000", "available": "24/7"},
    {"name": "Suicide Prevention Services", "phone": "2382 0000", "available": "24/7"},
    {"name": "The Samaritan Befrienders Hong Kong", "phone": "2389 2222", "available": "24/7"},
    {"name": "Emergency Services", "phone": "999", "available": "24/7"},
]


@dataclass
class SafetyAssessment:
    risk_level: RiskLevel
    show_crisis_banner: bool
    crisis_resources: list[dict[str, str]]
    detected_patterns: list[str]


def assess_safety(message: str) -> SafetyAssessment:
    detected: list[str] = []

    for pattern in _HIGH_RISK_PATTERNS:
        match = pattern.search(message)
        if match:
            detected.append(match.group())
            logger.warning(
                "safety_high_risk_detected pattern=%s",
                pattern.pattern,
            )
            return SafetyAssessment(
                risk_level="high",
                show_crisis_banner=True,
                crisis_resources=HK_CRISIS_RESOURCES,
                detected_patterns=detected,
            )

    for pattern in _MEDIUM_RISK_PATTERNS:
        match = pattern.search(message)
        if match:
            detected.append(match.group())

    if detected:
        logger.info(
            "safety_medium_risk_detected count=%d",
            len(detected),
        )
        return SafetyAssessment(
            risk_level="medium",
            show_crisis_banner=False,
            crisis_resources=HK_CRISIS_RESOURCES,
            detected_patterns=detected,
        )

    return SafetyAssessment(
        risk_level="low",
        show_crisis_banner=False,
        crisis_resources=[],
        detected_patterns=[],
    )
