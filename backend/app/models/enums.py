import enum


class RoleType(str, enum.Enum):
    companion = "companion"
    local_guide = "local_guide"
    study_guide = "study_guide"


class SafetyRiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class MemoryEntryType(str, enum.Enum):
    profile_fact = "profile_fact"
    preference = "preference"
    retrieval_document = "retrieval_document"
    summary = "summary"


class ProviderEventStatus(str, enum.Enum):
    success = "success"
    degraded = "degraded"
    failed = "failed"
    fallback = "fallback"


class ProviderEventScope(str, enum.Enum):
    chat = "chat"
    weather = "weather"
    maps = "maps"
    retrieval = "retrieval"
    voice = "voice"
    safety = "safety"


class AuditEventType(str, enum.Enum):
    memory_write = "memory_write"
    safety_event = "safety_event"
    recommendation_request = "recommendation_request"
    provider_call = "provider_call"
    user_profile_update = "user_profile_update"
    family_mode_share = "family_mode_share"
    error = "error"


class TravelMode(str, enum.Enum):
    walking = "walking"
    transit = "transit"
    driving = "driving"


class VoiceEventStatus(str, enum.Enum):
    success = "success"
    failed = "failed"
    degraded = "degraded"


class FamilyConsentScope(str, enum.Enum):
    summary_card = "summary_card"
    periodic_updates = "periodic_updates"


class FamilyShareStatus(str, enum.Enum):
    pending = "pending"
    shared = "shared"
    failed = "failed"
