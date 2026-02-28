from pathlib import Path
import subprocess
import sys

from sqlalchemy import UniqueConstraint

from app.models.chat import ChatThread


def test_initial_migration_contains_core_schema_artifacts() -> None:
    versions_dir = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    migration_files = sorted(versions_dir.glob("*.py"))

    assert migration_files, "expected at least one alembic migration file"
    migration_content = "\n".join(file.read_text(
        encoding="utf-8") for file in migration_files)

    assert "CREATE EXTENSION IF NOT EXISTS vector" in migration_content
    assert "uq_chat_threads_user_role_thread" in migration_content
    assert "recommendation_requests" in migration_content
    assert "memory_embeddings" in migration_content


def test_chat_thread_uses_role_scoped_identity_constraint() -> None:
    constraints = [
        constraint
        for constraint in ChatThread.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    ]
    unique_column_sets = {
        tuple(column.name for column in constraint.columns)
        for constraint in constraints
    }
    assert ("user_id", "role", "thread_id") in unique_column_sets


def test_offline_migration_sql_does_not_duplicate_enum_create_statements() -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    command = [sys.executable, "-m", "alembic", "upgrade", "head", "--sql"]
    result = subprocess.run(
        command,
        cwd=backend_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    sql_output = result.stdout

    assert sql_output.count("CREATE TYPE role_type AS ENUM") == 1
    assert sql_output.count("CREATE TYPE safety_risk_level AS ENUM") == 1
    assert sql_output.count("CREATE TYPE memory_entry_type AS ENUM") == 1
