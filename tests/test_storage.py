import pytest
import json
from pathlib import Path
from src.storage import Storage
import tempfile
import shutil

@pytest.fixture
def temp_storage():
    """Create temporary storage for testing."""
    temp_dir = tempfile.mkdtemp()
    storage = Storage(data_dir=temp_dir)
    yield storage
    shutil.rmtree(temp_dir)


def test_save_and_load_active_session(temp_storage):
    """Test saving and loading active session."""
    temp_storage.save_active_session("test task", "2025-01-01T10:00:00")
    
    active = temp_storage.load_active_session()
    assert active is not None
    assert active['task'] == "test task"
    assert active['start_time'] == "2025-01-01T10:00:00"


def test_load_active_session_when_none(temp_storage):
    """Test loading when no active session exists."""
    active = temp_storage.load_active_session()
    assert active is None


def test_clear_active_session(temp_storage):
    """Test clearing active session."""
    temp_storage.save_active_session("test", "2025-01-01T10:00:00")
    temp_storage.clear_active_session()
    
    active = temp_storage.load_active_session()
    assert active is None


def test_save_completed_session(temp_storage):
    """Test saving completed session to history."""
    temp_storage.save_completed_session(
        task="completed task",
        start_time="2025-01-01T10:00:00",
        end_time="2025-01-01T11:30:00",
        duration_seconds=5400
    )
    
    history = temp_storage.load_history()
    assert len(history) == 1
    assert history[0]['task'] == "completed task"
    assert history[0]['duration_seconds'] == 5400


def test_load_history_when_empty(temp_storage):
    """Test loading history when no sessions exist."""
    history = temp_storage.load_history()
    assert history == []