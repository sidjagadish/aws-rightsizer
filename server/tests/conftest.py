# tests/conftest.py
import subprocess
import pytest

@pytest.fixture(scope="session", autouse=True)
def _run_migrations_at_start():
    """Apply migrations once at the very start of the test session."""
    result = subprocess.run(
        "poetry run alembic upgrade head",
        shell=True, capture_output=True, text=True,
    )
    assert result.returncode == 0, f"Migration failed:\n{result.stderr}"