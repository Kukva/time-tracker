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


# ============ CSV EXPORT TESTS ============

def test_export_csv_with_sessions(tracker, tmp_path):
    """Test exporting sessions to CSV file."""
    # Add test sessions
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

    output_file = tmp_path / "test_export.csv"
    result = tracker.export_csv(str(output_file))

    assert "Exported" in result
    assert "2 sessions" in result
    assert output_file.exists()

    # Verify CSV content
    import csv
    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2
    assert rows[0]['task'] == "morning work"
    assert rows[0]['duration_hours'] == "2"
    assert rows[1]['task'] == "afternoon work"


def test_export_csv_no_sessions(tracker, tmp_path):
    """Test export when no sessions exist."""
    output_file = tmp_path / "empty_export.csv"
    result = tracker.export_csv(str(output_file))

    assert "No sessions to export" in result
    assert not output_file.exists()


def test_export_csv_with_date_filter(tracker, tmp_path):
    """Test CSV export with date range filtering."""
    # Add sessions from different dates
    tracker.storage.save_completed_session(
        task="old task",
        start_time="2026-01-01T10:00:00",
        end_time="2026-01-01T11:00:00",
        duration_seconds=3600
    )
    tracker.storage.save_completed_session(
        task="recent task",
        start_time="2026-01-14T10:00:00",
        end_time="2026-01-14T11:00:00",
        duration_seconds=3600
    )

    output_file = tmp_path / "filtered_export.csv"
    result = tracker.export_csv(
        str(output_file),
        start_date="2026-01-10",
        end_date="2026-01-20"
    )

    assert "Exported 1 sessions" in result
    assert output_file.exists()

    # Verify only recent task in CSV
    import csv
    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    assert rows[0]['task'] == "recent task"


def test_export_csv_auto_adds_extension(tracker, tmp_path):
    """Test that .csv extension is added automatically."""
    # Add a session
    today = datetime.now().date().isoformat()
    tracker.storage.save_completed_session(
        task="test",
        start_time=f"{today}T10:00:00",
        end_time=f"{today}T11:00:00",
        duration_seconds=3600
    )

    output_file = tmp_path / "report"  # No extension
    result = tracker.export_csv(str(output_file))

    assert "Exported" in result
    # Should create report.csv
    csv_file = tmp_path / "report.csv"
    assert csv_file.exists()


def test_export_csv_default_filename(tracker):
    """Test export with default filename."""
    # Add a session
    today = datetime.now().date().isoformat()
    tracker.storage.save_completed_session(
        task="test",
        start_time=f"{today}T10:00:00",
        end_time=f"{today}T11:00:00",
        duration_seconds=3600
    )

    result = tracker.export_csv()

    assert "Exported" in result
    assert "time_tracker_export.csv" in result


def test_export_csv_skips_corrupted_sessions(tracker, tmp_path):
    """Test that export handles corrupted session data gracefully."""
    # Add valid session
    today = datetime.now().date().isoformat()
    tracker.storage.save_completed_session(
        task="valid task",
        start_time=f"{today}T10:00:00",
        end_time=f"{today}T11:00:00",
        duration_seconds=3600
    )

    # Manually add corrupted session
    history = tracker.storage.load_history()
    history.append({"invalid": "data"})
    import json
    with open(tracker.storage.history_file, 'w') as f:
        json.dump(history, f)

    output_file = tmp_path / "export_with_corruption.csv"
    result = tracker.export_csv(str(output_file))

    # Should still export valid session
    assert "Exported" in result
    assert output_file.exists()

    import csv
    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    assert rows[0]['task'] == "valid task"
