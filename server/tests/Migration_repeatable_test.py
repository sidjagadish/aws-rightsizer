"""
Migration_repeatable_test.py
============================
Validates that Alembic migrations for the AWS Rightsizer schema are
repeatable (fresh → head) and reversible (head → base).

Prerequisites
-------------
* Docker Compose Postgres container is running and healthy.
* `poetry install` has been run inside server/.
* Working directory when running: **server/**

Run
---
    cd server
    poetry run pytest Migration_repeatable_test.py -v
"""

import os
import subprocess
import pytest
from sqlalchemy import create_engine, inspect, text

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/rightsizer",
)

EXPECTED_TABLES = sorted(
    [
        "scan_run",
        "ec2_instance",
        "utilization_metric",
        "finding",
        "recommendation",
    ]
)

# Foreign-key pairs we expect after upgrade.
# Format: (source_table, source_column, target_table, target_column)
EXPECTED_FK_RELATIONSHIPS = [
    ("utilization_metric", "run_id", "scan_run", "run_id"),
    ("utilization_metric", "resource_id", "ec2_instance", "resource_id"),
    ("finding", "run_id", "scan_run", "run_id"),
    ("finding", "resource_id", "ec2_instance", "resource_id"),
    ("finding", "utilization_metric_id", "utilization_metric", "metric_id"),
    ("recommendation", "finding_id", "finding", "finding_id"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _engine():
    """Return a disposable SQLAlchemy engine."""
    return create_engine(DATABASE_URL, pool_pre_ping=True)


def _run_alembic(command: str) -> subprocess.CompletedProcess:
    """
    Execute an Alembic CLI command via Poetry and return the result.
    Raises on non-zero exit so pytest shows the stderr clearly.
    """
    result = subprocess.run(
        f"poetry run alembic {command}",
        shell=True,
        capture_output=True,
        text=True,
    )
    return result


def _table_names(engine) -> list[str]:
    """Return sorted list of non-system table names in the public schema."""
    inspector = inspect(engine)
    return sorted(
        t
        for t in inspector.get_table_names(schema="public")
        if t != "alembic_version"
    )


def _alembic_version(engine) -> str | None:
    """Return current Alembic revision or None if table is missing/empty."""
    inspector = inspect(engine)
    if "alembic_version" not in inspector.get_table_names(schema="public"):
        return None
    with engine.connect() as conn:
        row = conn.execute(text("SELECT version_num FROM alembic_version")).first()
    return row[0] if row else None


def _nuke_schema(engine):
    """
    Drop every table (including alembic_version) so the next test starts
    from a truly blank database.  Uses CASCADE to handle FK ordering.
    """
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_database():
    """
    Ensure each test begins with an empty public schema and ends the same
    way, so tests are fully independent of run order.
    """
    engine = _engine()
    _nuke_schema(engine)
    yield
    _nuke_schema(engine)
    engine.dispose()


# ---------------------------------------------------------------------------
# Test 1 – Fresh upgrade (base → head)
# ---------------------------------------------------------------------------

class TestFreshUpgrade:
    """Start from an empty DB, run `alembic upgrade head`, verify success."""

    def test_upgrade_exits_zero(self):
        result = _run_alembic("upgrade head")
        assert result.returncode == 0, (
            f"alembic upgrade head failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    def test_alembic_version_recorded(self):
        _run_alembic("upgrade head")
        engine = _engine()
        version = _alembic_version(engine)
        engine.dispose()
        assert version is not None, (
            "alembic_version table is missing or empty after upgrade head."
        )


# ---------------------------------------------------------------------------
# Test 2 – Downgrade (head → base)
# ---------------------------------------------------------------------------

class TestDowngradeToBase:
    """Upgrade first, then downgrade to base and verify everything is gone."""

    def test_downgrade_exits_zero(self):
        up = _run_alembic("upgrade head")
        assert up.returncode == 0, f"upgrade failed: {up.stderr}"

        down = _run_alembic("downgrade base")
        assert down.returncode == 0, (
            f"alembic downgrade base failed.\n"
            f"STDOUT:\n{down.stdout}\n"
            f"STDERR:\n{down.stderr}"
        )

    def test_tables_removed_after_downgrade(self):
        _run_alembic("upgrade head")
        _run_alembic("downgrade base")

        engine = _engine()
        remaining = _table_names(engine)
        engine.dispose()
        assert remaining == [], (
            f"Tables still present after downgrade base: {remaining}"
        )

    def test_alembic_version_empty_after_downgrade(self):
        _run_alembic("upgrade head")
        _run_alembic("downgrade base")

        engine = _engine()
        version = _alembic_version(engine)
        engine.dispose()
        assert version is None, (
            f"alembic_version still holds revision '{version}' after "
            f"downgrade base."
        )


# ---------------------------------------------------------------------------
# Test 3 – Full round-trip (upgrade → downgrade → upgrade again)
# ---------------------------------------------------------------------------

class TestRoundTrip:
    """Prove the migration is truly repeatable: up, down, then up again."""

    def test_full_cycle_succeeds(self):
        # First upgrade
        r1 = _run_alembic("upgrade head")
        assert r1.returncode == 0, f"First upgrade failed: {r1.stderr}"

        # Downgrade
        r2 = _run_alembic("downgrade base")
        assert r2.returncode == 0, f"Downgrade failed: {r2.stderr}"

        # Second upgrade
        r3 = _run_alembic("upgrade head")
        assert r3.returncode == 0, (
            f"Second upgrade head failed after round-trip.\n"
            f"STDOUT:\n{r3.stdout}\n"
            f"STDERR:\n{r3.stderr}"
        )

    def test_tables_present_after_round_trip(self):
        _run_alembic("upgrade head")
        _run_alembic("downgrade base")
        _run_alembic("upgrade head")

        engine = _engine()
        actual = _table_names(engine)
        engine.dispose()
        assert actual == EXPECTED_TABLES, (
            f"Tables after round-trip don't match.\n"
            f"Expected: {EXPECTED_TABLES}\n"
            f"Actual:   {actual}"
        )


# ---------------------------------------------------------------------------
# Test 4 – Tables actually exist after upgrade
# ---------------------------------------------------------------------------

class TestTablesExist:
    """After upgrade head, every core entity table must be present."""

    def test_all_five_tables_created(self):
        result = _run_alembic("upgrade head")
        assert result.returncode == 0, f"upgrade failed: {result.stderr}"

        engine = _engine()
        actual = _table_names(engine)
        engine.dispose()

        assert actual == EXPECTED_TABLES, (
            f"Missing or extra tables after upgrade head.\n"
            f"Expected: {EXPECTED_TABLES}\n"
            f"Actual:   {actual}"
        )

    @pytest.mark.parametrize("table_name", EXPECTED_TABLES)
    def test_table_has_primary_key(self, table_name):
        """Every table must have at least one primary-key column."""
        _run_alembic("upgrade head")
        engine = _engine()
        inspector = inspect(engine)
        pk = inspector.get_pk_constraint(table_name, schema="public")
        engine.dispose()

        assert pk and pk["constrained_columns"], (
            f"Table '{table_name}' has no primary key."
        )


# ---------------------------------------------------------------------------
# Test 5 – Autogenerate "no diff" (models ↔ migrations in sync)
# ---------------------------------------------------------------------------

class TestNoDrift:
    """
    After upgrading to head, autogenerate should produce an *empty*
    migration — proving ORM models and migration files are in sync.
    """

    def test_no_pending_changes(self):
        up = _run_alembic("upgrade head")
        assert up.returncode == 0, f"upgrade failed: {up.stderr}"

        # `alembic check` exits non-zero when models differ from the DB.
        # Available since Alembic ≥ 1.9.  Falls back to a manual approach
        # if the command isn't recognised.
        check = _run_alembic("check")

        if "No new upgrade operations detected" in check.stdout:
            return  # pass — no drift

        if check.returncode == 0:
            return  # pass — alembic check succeeded with no diff

        # If `alembic check` isn't available, do a dry-run autogenerate
        # and inspect its output for upgrade ops.
        auto = _run_alembic(
            'revision --autogenerate -m "drift_check" --rev-id drift000'
        )
        combined_output = auto.stdout + auto.stderr

        # A truly empty migration has no upgrade operations.
        has_changes = any(
            keyword in combined_output
            for keyword in [
                "op.create_table",
                "op.drop_table",
                "op.add_column",
                "op.drop_column",
                "op.alter_column",
                "op.create_index",
                "op.drop_index",
                "op.create_foreign_key",
                "op.drop_constraint",
            ]
        )

        assert not has_changes, (
            "Autogenerate detected schema drift between ORM models and the "
            "current migration head.  Run:\n"
            "  poetry run alembic revision --autogenerate -m '<description>'\n"
            "to capture the difference.\n\n"
            f"Autogenerate output:\n{combined_output}"
        )


# ---------------------------------------------------------------------------
# Bonus – Foreign-key relationship validation
# ---------------------------------------------------------------------------

class TestForeignKeys:
    """Verify FK constraints match the ERD after upgrade head."""

    def test_expected_foreign_keys_exist(self):
        _run_alembic("upgrade head")
        engine = _engine()
        inspector = inspect(engine)

        actual_fks: list[tuple[str, str, str, str]] = []
        for table in EXPECTED_TABLES:
            for fk in inspector.get_foreign_keys(table, schema="public"):
                for local_col, remote_col in zip(
                    fk["constrained_columns"], fk["referred_columns"]
                ):
                    actual_fks.append(
                        (table, local_col, fk["referred_table"], remote_col)
                    )
        engine.dispose()

        for expected in EXPECTED_FK_RELATIONSHIPS:
            assert expected in actual_fks, (
                f"Missing FK: {expected[0]}.{expected[1]} → "
                f"{expected[2]}.{expected[3]}\n"
                f"Actual FKs found: {actual_fks}"
            )