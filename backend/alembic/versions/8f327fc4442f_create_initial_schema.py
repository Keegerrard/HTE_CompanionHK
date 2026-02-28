"""create initial schema

Revision ID: 8f327fc4442f
Revises: 
Create Date: 2026-02-28 12:23:47.695396

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '8f327fc4442f'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

role_type = postgresql.ENUM(
    "companion",
    "local_guide",
    "study_guide",
    name="role_type",
    create_type=False,
)
safety_risk_level = postgresql.ENUM(
    "low",
    "medium",
    "high",
    name="safety_risk_level",
    create_type=False,
)
memory_entry_type = postgresql.ENUM(
    "profile_fact",
    "preference",
    "retrieval_document",
    "summary",
    name="memory_entry_type",
    create_type=False,
)
provider_event_scope = postgresql.ENUM(
    "chat",
    "weather",
    "maps",
    "retrieval",
    "voice",
    "safety",
    name="provider_event_scope",
    create_type=False,
)
provider_event_status = postgresql.ENUM(
    "success",
    "degraded",
    "failed",
    "fallback",
    name="provider_event_status",
    create_type=False,
)
audit_event_type = postgresql.ENUM(
    "memory_write",
    "safety_event",
    "recommendation_request",
    "provider_call",
    "user_profile_update",
    "family_mode_share",
    "error",
    name="audit_event_type",
    create_type=False,
)
travel_mode = postgresql.ENUM(
    "walking",
    "transit",
    "driving",
    name="travel_mode",
    create_type=False,
)
voice_event_status = postgresql.ENUM(
    "success",
    "failed",
    "degraded",
    name="voice_event_status",
    create_type=False,
)
family_consent_scope = postgresql.ENUM(
    "summary_card",
    "periodic_updates",
    name="family_consent_scope",
    create_type=False,
)
family_share_status = postgresql.ENUM(
    "pending",
    "shared",
    "failed",
    name="family_share_status",
    create_type=False,
)


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    role_type.create(bind, checkfirst=True)
    safety_risk_level.create(bind, checkfirst=True)
    memory_entry_type.create(bind, checkfirst=True)
    provider_event_scope.create(bind, checkfirst=True)
    provider_event_status.create(bind, checkfirst=True)
    audit_event_type.create(bind, checkfirst=True)
    travel_mode.create(bind, checkfirst=True)
    voice_event_status.create(bind, checkfirst=True)
    family_consent_scope.create(bind, checkfirst=True)
    family_share_status.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("user_id", sa.String(length=128), primary_key=True),
        sa.Column("display_name", sa.String(length=128), nullable=True),
        sa.Column("locale", sa.String(length=16), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=True),
        sa.Column("is_active", sa.Boolean(),
                  nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "user_profiles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=128), sa.ForeignKey(
            "users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("profile_key", sa.String(length=128), nullable=False),
        sa.Column("profile_value", sa.Text(), nullable=False),
        sa.Column("is_sensitive", sa.Boolean(),
                  nullable=False, server_default=sa.false()),
        sa.Column("source", sa.String(length=64), nullable=False,
                  server_default=sa.text("'explicit'")),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "profile_key",
                            name="uq_user_profiles_user_id_key"),
    )
    op.create_index("ix_user_profiles_user_id", "user_profiles", ["user_id"])

    op.create_table(
        "user_preferences",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=128), sa.ForeignKey(
            "users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", role_type, nullable=True),
        sa.Column("preference_tag", sa.String(length=128), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False,
                  server_default=sa.text("1.0")),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "role", "preference_tag",
                            name="uq_user_preferences_user_role_tag"),
    )
    op.create_index("ix_user_preferences_user_id_role",
                    "user_preferences", ["user_id", "role"])

    op.create_table(
        "chat_threads",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=128), sa.ForeignKey(
            "users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", role_type, nullable=False),
        sa.Column("thread_id", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "role", "thread_id",
                            name="uq_chat_threads_user_role_thread"),
    )
    op.create_index("ix_chat_threads_user_role_activity",
                    "chat_threads", ["user_id", "role", "updated_at"])

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("thread_pk", sa.String(length=36), sa.ForeignKey(
            "chat_threads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(length=128), sa.ForeignKey(
            "users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", role_type, nullable=False),
        sa.Column("thread_id", sa.String(length=128), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("user_message", sa.Text(), nullable=False),
        sa.Column("assistant_reply", sa.Text(), nullable=False),
        sa.Column("runtime", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("provider_fallback_reason",
                  sa.String(length=128), nullable=True),
        sa.Column("context_snapshot", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_chat_messages_thread_created",
                    "chat_messages", ["thread_id", "created_at"])
    op.create_index("ix_chat_messages_request_id",
                    "chat_messages", ["request_id"])
    op.create_index("ix_chat_messages_user_role_created",
                    "chat_messages", ["user_id", "role", "created_at"])

    op.create_table(
        "safety_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("chat_message_id", sa.String(length=36), sa.ForeignKey(
            "chat_messages.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("thread_pk", sa.String(length=36), sa.ForeignKey(
            "chat_threads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(length=128), sa.ForeignKey(
            "users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", role_type, nullable=False),
        sa.Column("thread_id", sa.String(length=128), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("risk_level", safety_risk_level, nullable=False),
        sa.Column("show_crisis_banner", sa.Boolean(),
                  nullable=False, server_default=sa.false()),
        sa.Column("emotion_label", sa.String(length=64), nullable=True),
        sa.Column("emotion_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_safety_events_user_risk_created", "safety_events", [
                    "user_id", "risk_level", "created_at"])
    op.create_index("ix_safety_events_request_id",
                    "safety_events", ["request_id"])

    op.create_table(
        "memory_entries",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=128), sa.ForeignKey(
            "users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", role_type, nullable=True),
        sa.Column("thread_id", sa.String(length=128), nullable=True),
        sa.Column("entry_type", memory_entry_type, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_sensitive", sa.Boolean(),
                  nullable=False, server_default=sa.false()),
        sa.Column("write_reason", sa.String(length=128), nullable=False),
        sa.Column("source_provider", sa.String(length=64), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_by_request_id",
                  sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_memory_entries_user_role_type_created",
        "memory_entries",
        ["user_id", "role", "entry_type", "created_at"],
    )
    op.create_index("ix_memory_entries_thread_id",
                    "memory_entries", ["thread_id"])

    op.create_table(
        "memory_embeddings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("memory_entry_id", sa.String(length=36), sa.ForeignKey(
            "memory_entries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(length=128), sa.ForeignKey(
            "users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", role_type, nullable=True),
        sa.Column("embedding_model", sa.String(length=128), nullable=False),
        sa.Column("embedding_dimensions", sa.Integer(), nullable=False),
        sa.Column("distance_metric", sa.String(length=24),
                  nullable=False, server_default=sa.text("'cosine'")),
        sa.Column("embedding", Vector(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("memory_entry_id", "embedding_model",
                            name="uq_memory_embeddings_entry_model"),
    )
    op.create_index("ix_memory_embeddings_user_role",
                    "memory_embeddings", ["user_id", "role"])
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_memory_embeddings_embedding_hnsw "
        "ON memory_embeddings USING hnsw (embedding vector_cosine_ops)"
    )

    op.create_table(
        "recommendation_requests",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("request_id", sa.String(length=64),
                  nullable=False, unique=True),
        sa.Column("user_id", sa.String(length=128), sa.ForeignKey(
            "users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", role_type, nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("max_results", sa.Integer(), nullable=False),
        sa.Column("preference_tags", sa.JSON(), nullable=False),
        sa.Column("travel_mode", travel_mode, nullable=False),
        sa.Column("user_location_geohash",
                  sa.String(length=16), nullable=True),
        sa.Column("user_location_region", sa.String(
            length=128), nullable=True),
        sa.Column("weather_condition", sa.String(length=32), nullable=True),
        sa.Column("temperature_c", sa.Float(), nullable=True),
        sa.Column("degraded", sa.Boolean(), nullable=False,
                  server_default=sa.false()),
        sa.Column("fallback_reason", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_recommendation_requests_user_role_created",
        "recommendation_requests",
        ["user_id", "role", "created_at"],
    )
    op.create_index("ix_recommendation_requests_request_id",
                    "recommendation_requests", ["request_id"])

    op.create_table(
        "recommendation_items",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "recommendation_request_id",
            sa.String(length=36),
            sa.ForeignKey("recommendation_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("place_id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("user_ratings_total", sa.Integer(), nullable=True),
        sa.Column("types", sa.JSON(), nullable=False),
        sa.Column("place_latitude", sa.Float(), nullable=False),
        sa.Column("place_longitude", sa.Float(), nullable=False),
        sa.Column("photo_url", sa.Text(), nullable=True),
        sa.Column("maps_uri", sa.Text(), nullable=True),
        sa.Column("distance_text", sa.String(length=32), nullable=True),
        sa.Column("duration_text", sa.String(length=32), nullable=True),
        sa.Column("fit_score", sa.Float(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("fit_score >= 0.0 AND fit_score <= 1.0",
                           name="ck_recommendation_items_fit_score_range"),
    )
    op.create_index("ix_recommendation_items_request_id",
                    "recommendation_items", ["recommendation_request_id"])
    op.create_index("ix_recommendation_items_place_id",
                    "recommendation_items", ["place_id"])

    op.create_table(
        "provider_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=128), sa.ForeignKey(
            "users.user_id", ondelete="SET NULL"), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("role", role_type, nullable=True),
        sa.Column("scope", provider_event_scope, nullable=False),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("runtime", sa.String(length=64), nullable=True),
        sa.Column("status", provider_event_status, nullable=False),
        sa.Column("fallback_reason", sa.String(length=128), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_provider_events_request_id",
                    "provider_events", ["request_id"])
    op.create_index("ix_provider_events_user_created",
                    "provider_events", ["user_id", "created_at"])

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=128), sa.ForeignKey(
            "users.user_id", ondelete="SET NULL"), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("role", role_type, nullable=True),
        sa.Column("thread_id", sa.String(length=128), nullable=True),
        sa.Column("event_type", audit_event_type, nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_audit_events_event_type_created",
                    "audit_events", ["event_type", "created_at"])
    op.create_index("ix_audit_events_user_created",
                    "audit_events", ["user_id", "created_at"])

    op.create_table(
        "voice_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=128), sa.ForeignKey(
            "users.user_id", ondelete="SET NULL"), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("text_hash", sa.String(length=128), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=True),
        sa.Column("status", voice_event_status, nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("audio_uri", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_voice_events_request_id",
                    "voice_events", ["request_id"])
    op.create_index("ix_voice_events_user_created",
                    "voice_events", ["user_id", "created_at"])

    op.create_table(
        "family_share_consents",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=128), sa.ForeignKey(
            "users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("contact_label", sa.String(length=160), nullable=False),
        sa.Column("consent_scope", family_consent_scope, nullable=False),
        sa.Column("is_active", sa.Boolean(),
                  nullable=False, server_default=sa.true()),
        sa.Column("granted_by_request_id",
                  sa.String(length=64), nullable=True),
        sa.Column("revoked_by_request_id",
                  sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint(
            "user_id",
            "contact_label",
            "consent_scope",
            name="uq_family_share_consents_user_contact_scope",
        ),
    )
    op.create_index("ix_family_share_consents_user_active",
                    "family_share_consents", ["user_id", "is_active"])

    op.create_table(
        "family_share_cards",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "consent_id",
            sa.String(length=36),
            sa.ForeignKey("family_share_consents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_id", sa.String(length=128), sa.ForeignKey(
            "users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", role_type, nullable=True),
        sa.Column("thread_id", sa.String(length=128), nullable=True),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("share_status", family_share_status,
                  nullable=False, server_default=sa.text("'pending'")),
        sa.Column("shared_with", sa.String(length=160), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_family_share_cards_user_created",
                    "family_share_cards", ["user_id", "created_at"])
    op.create_index("ix_family_share_cards_status",
                    "family_share_cards", ["share_status"])


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()

    op.drop_index("ix_family_share_cards_status",
                  table_name="family_share_cards")
    op.drop_index("ix_family_share_cards_user_created",
                  table_name="family_share_cards")
    op.drop_table("family_share_cards")

    op.drop_index("ix_family_share_consents_user_active",
                  table_name="family_share_consents")
    op.drop_table("family_share_consents")

    op.drop_index("ix_voice_events_user_created", table_name="voice_events")
    op.drop_index("ix_voice_events_request_id", table_name="voice_events")
    op.drop_table("voice_events")

    op.drop_index("ix_audit_events_user_created", table_name="audit_events")
    op.drop_index("ix_audit_events_event_type_created",
                  table_name="audit_events")
    op.drop_table("audit_events")

    op.drop_index("ix_provider_events_user_created",
                  table_name="provider_events")
    op.drop_index("ix_provider_events_request_id",
                  table_name="provider_events")
    op.drop_table("provider_events")

    op.drop_index("ix_recommendation_items_place_id",
                  table_name="recommendation_items")
    op.drop_index("ix_recommendation_items_request_id",
                  table_name="recommendation_items")
    op.drop_table("recommendation_items")

    op.drop_index("ix_recommendation_requests_request_id",
                  table_name="recommendation_requests")
    op.drop_index("ix_recommendation_requests_user_role_created",
                  table_name="recommendation_requests")
    op.drop_table("recommendation_requests")

    op.execute("DROP INDEX IF EXISTS ix_memory_embeddings_embedding_hnsw")
    op.drop_index("ix_memory_embeddings_user_role",
                  table_name="memory_embeddings")
    op.drop_table("memory_embeddings")

    op.drop_index("ix_memory_entries_thread_id", table_name="memory_entries")
    op.drop_index("ix_memory_entries_user_role_type_created",
                  table_name="memory_entries")
    op.drop_table("memory_entries")

    op.drop_index("ix_safety_events_request_id", table_name="safety_events")
    op.drop_index("ix_safety_events_user_risk_created",
                  table_name="safety_events")
    op.drop_table("safety_events")

    op.drop_index("ix_chat_messages_user_role_created",
                  table_name="chat_messages")
    op.drop_index("ix_chat_messages_request_id", table_name="chat_messages")
    op.drop_index("ix_chat_messages_thread_created",
                  table_name="chat_messages")
    op.drop_table("chat_messages")

    op.drop_index("ix_chat_threads_user_role_activity",
                  table_name="chat_threads")
    op.drop_table("chat_threads")

    op.drop_index("ix_user_preferences_user_id_role",
                  table_name="user_preferences")
    op.drop_table("user_preferences")

    op.drop_index("ix_user_profiles_user_id", table_name="user_profiles")
    op.drop_table("user_profiles")

    op.drop_table("users")

    family_share_status.drop(bind, checkfirst=True)
    family_consent_scope.drop(bind, checkfirst=True)
    voice_event_status.drop(bind, checkfirst=True)
    travel_mode.drop(bind, checkfirst=True)
    audit_event_type.drop(bind, checkfirst=True)
    provider_event_status.drop(bind, checkfirst=True)
    provider_event_scope.drop(bind, checkfirst=True)
    memory_entry_type.drop(bind, checkfirst=True)
    safety_risk_level.drop(bind, checkfirst=True)
    role_type.drop(bind, checkfirst=True)
