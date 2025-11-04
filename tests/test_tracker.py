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