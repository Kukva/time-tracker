import pytest
from src.tracker import TimeTracker
from src.storage import Storage
import tempfile
import shutil
from datetime import datetime

@pytest.fixture
def tracker():
    """Create tracker with temporary storage."""
    temp_dir = tempfile.mkdtemp()
    tracker = TimeTracker()
    tracker.storage = Storage(data_dir=temp_dir)
    yield tracker
    shutil.rmtree(temp_dir)


# ============ EXISTING TESTS ============

def test_start_new_session(tracker):
    """Test starting a new session."""
    result = tracker.start("coding homework")
    
    assert "Session started" in result
    assert "coding homework" in result
    
    active = tracker.storage.load_active_session()
    assert active is not None
    assert active['task'] == "coding homework"


def test_cannot_start_when_already_tracking(tracker):
    """Test that starting second session fails."""
    tracker.start("first task")
    result = tracker.start("second task")
    
    assert "Already tracking" in result
    assert "first task" in result
    
    # Verify first task still active
    active = tracker.storage.load_active_session()
    assert active['task'] == "first task"


def test_stop_active_session(tracker):
    """Test stopping an active session."""
    tracker.start("test task")
    result = tracker.stop()
    
    assert "Session stopped" in result
    assert "test task" in result
    assert "Duration" in result
    
    # Verify session cleared
    active = tracker.storage.load_active_session()
    assert active is None
    
    # Verify saved to history
    history = tracker.storage.load_history()
    assert len(history) == 1
    assert history[0]['task'] == "test task"


def test_stop_when_no_active_session(tracker):
    """Test stopping when nothing is tracking."""
    result = tracker.stop()
    assert "No active session" in result


def test_status_when_tracking(tracker):
    """Test status shows current task."""
    tracker.start("active task")
    result = tracker.status()
    
    assert "active task" in result
    assert "Elapsed" in result


def test_status_when_not_tracking(tracker):
    """Test status when no active session."""
    result = tracker.status()
    assert "No active session" in result


def test_report_with_sessions(tracker):
    """Test report shows completed sessions."""
    # Simulate completed sessions
    today = datetime.now().date().isoformat()
    tracker.storage.save_completed_session(
        task="morning work",
        start_time=f"{today}T09:00:00",
        end_time=f"{today}T11:00:00",
        duration_seconds=7200
    )
    tracker.storage.save_completed_session(
        task="afternoon work",
        start_time=f"{today}T14:00:00",
        end_time=f"{today}T16:30:00",
        duration_seconds=9000
    )
    
    result = tracker.report()
    
    assert "Report for" in result
    assert "morning work" in result
    assert "afternoon work" in result
    assert "Total" in result


def test_report_when_no_sessions(tracker):
    """Test report when no sessions recorded."""
    result = tracker.report()
    assert "No sessions recorded" in result


# ============ NEW VALIDATION TESTS ============

def test_start_with_empty_task_name(tracker):
    """Test that empty task name is rejected."""
    result = tracker.start("")
    assert "cannot be empty" in result
    
    # Verify no session created
    active = tracker.storage.load_active_session()
    assert active is None


def test_start_with_whitespace_only_task(tracker):
    """Test that whitespace-only task name is rejected."""
    result = tracker.start("   ")
    assert "cannot be empty" in result
    
    active = tracker.storage.load_active_session()
    assert active is None


def test_start_with_too_long_task_name(tracker):
    """Test that task names over 100 chars are rejected."""
    long_task = "a" * 101
    result = tracker.start(long_task)
    
    assert "too long" in result
    assert "100" in result
    
    active = tracker.storage.load_active_session()
    assert active is None


def test_start_with_newline_in_task(tracker):
    """Test that newlines in task name are rejected."""
    result = tracker.start("task with\nnewline")
    assert "invalid character" in result
    
    active = tracker.storage.load_active_session()
    assert active is None


def test_start_trims_whitespace(tracker):
    """Test that leading/trailing whitespace is trimmed."""
    result = tracker.start("  task with spaces  ")
    assert "Session started" in result
    
    active = tracker.storage.load_active_session()
    assert active['task'] == "task with spaces"


def test_start_with_max_length_task(tracker):
    """Test that exactly 100 char task name works."""
    task = "a" * 100
    result = tracker.start(task)
    
    assert "Session started" in result
    
    active = tracker.storage.load_active_session()
    assert active is not None
    assert len(active['task']) == 100


# ============ CORRUPTED JSON TESTS ============

def test_load_corrupted_active_session(tracker):
    """Test that corrupted active.json is handled gracefully."""
    # Write invalid JSON
    with open(tracker.storage.active_file, 'w') as f:
        f.write("{invalid json content")
    
    # Should return None instead of crashing
    result = tracker.storage.load_active_session()
    assert result is None


def test_load_corrupted_history(tracker):
    """Test that corrupted sessions.json returns empty list."""
    # Write invalid JSON
    with open(tracker.storage.history_file, 'w') as f:
        f.write("[{broken json")
    
    # Should return empty list instead of crashing
    result = tracker.storage.load_history()
    assert result == []


def test_report_with_corrupted_history(tracker):
    """Test that report handles corrupted history gracefully."""
    # Write corrupted history
    with open(tracker.storage.history_file, 'w') as f:
        f.write("not valid json")
    
    result = tracker.report()
    assert "No sessions recorded" in result


def test_stop_with_invalid_active_session(tracker):
    """Test stopping when active session has invalid data."""
    # Create session with invalid timestamp
    tracker.storage.save_active_session("test", "invalid-timestamp")
    
    result = tracker.stop()
    assert "Error" in result or "invalid" in result.lower()
