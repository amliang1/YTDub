import pytest
import os
import sys
from pathlib import Path

# Ensure critical environment variables are present during test collection
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("POSTGRES_USER", "testuser")
os.environ.setdefault("POSTGRES_PASSWORD", "testpass")
os.environ.setdefault("POSTGRES_DB", "testdb")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables."""
    os.environ["TESTING"] = "true"
    # Minimal env to satisfy config.Settings validation during import
    os.environ.setdefault("POSTGRES_USER", "testuser")
    os.environ.setdefault("POSTGRES_PASSWORD", "testpass")
    os.environ.setdefault("POSTGRES_DB", "testdb")
    os.environ.setdefault("POSTGRES_HOST", "localhost")
    os.environ.setdefault("POSTGRES_PORT", "5432")
    os.environ.setdefault("REDIS_HOST", "localhost")
    os.environ.setdefault("REDIS_PORT", "6379")
    yield
    os.environ.pop("TESTING", None)
