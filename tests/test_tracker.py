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


# ============ WEEKLY REPORT TESTS ============

def test_weekly_report_current_week(tracker):
    """Test weekly report for current week."""
    from datetime import datetime, timedelta

    # Get current week's Monday
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())

    # Add sessions across the week
    for i in range(5):  # Mon-Fri
        day = monday + timedelta(days=i)
        date_str = day.date().isoformat()
        tracker.storage.save_completed_session(
            task=f"work day {i+1}",
            start_time=f"{date_str}T09:00:00",
            end_time=f"{date_str}T17:00:00",
            duration_seconds=28800  # 8 hours
        )

    result = tracker.report_weekly()

    assert "Week" in result
    assert "work day 1" in result
    assert "work day 5" in result
    assert "40h" in result  # 5 days * 8 hours


def test_weekly_report_specific_week(tracker):
    """Test weekly report for a specific week."""
    # Add sessions in week of 2026-01-05 (Monday)
    tracker.storage.save_completed_session(
        task="week 1 task",
        start_time="2026-01-06T10:00:00",  # Tuesday
        end_time="2026-01-06T12:00:00",
        duration_seconds=7200  # 2 hours
    )
    # Add session in different week
    tracker.storage.save_completed_session(
        task="week 2 task",
        start_time="2026-01-13T10:00:00",  # Next Monday
        end_time="2026-01-13T11:00:00",
        duration_seconds=3600
    )

    result = tracker.report_weekly(week_start="2026-01-06")

    assert "week 1 task" in result
    assert "week 2 task" not in result
    assert "2h" in result


def test_weekly_report_no_sessions(tracker):
    """Test weekly report when no sessions exist."""
    result = tracker.report_weekly()

    assert "No sessions recorded" in result


def test_weekly_report_groups_by_day(tracker):
    """Test that weekly report groups sessions by day."""
    # Add multiple sessions on same day
    tracker.storage.save_completed_session(
        task="morning work",
        start_time="2026-01-14T09:00:00",
        end_time="2026-01-14T12:00:00",
        duration_seconds=10800  # 3 hours
    )
    tracker.storage.save_completed_session(
        task="afternoon work",
        start_time="2026-01-14T14:00:00",
        end_time="2026-01-14T17:00:00",
        duration_seconds=10800  # 3 hours
    )

    result = tracker.report_weekly()

    assert "2026-01-14" in result
    assert "morning work" in result
    assert "afternoon work" in result
    assert "6h" in result  # Total for the day


# ============ MONTHLY REPORT TESTS ============

def test_monthly_report_current_month(tracker):
    """Test monthly report for current month."""
    from datetime import datetime

    today = datetime.now()
    month_str = today.strftime("%Y-%m")

    # Add sessions in current month
    for day in [5, 10, 15]:
        date_str = f"{month_str}-{day:02d}"
        tracker.storage.save_completed_session(
            task=f"work day {day}",
            start_time=f"{date_str}T09:00:00",
            end_time=f"{date_str}T17:00:00",
            duration_seconds=28800  # 8 hours
        )

    result = tracker.report_monthly()

    assert "Month" in result or month_str in result
    assert "work day 5" in result
    assert "work day 15" in result
    assert "24h" in result  # 3 days * 8 hours


def test_monthly_report_specific_month(tracker):
    """Test monthly report for a specific month."""
    # Add sessions in January 2026
    tracker.storage.save_completed_session(
        task="january task",
        start_time="2026-01-15T10:00:00",
        end_time="2026-01-15T14:00:00",
        duration_seconds=14400  # 4 hours
    )
    # Add session in different month
    tracker.storage.save_completed_session(
        task="february task",
        start_time="2026-02-10T10:00:00",
        end_time="2026-02-10T12:00:00",
        duration_seconds=7200
    )

    result = tracker.report_monthly(month="2026-01")

    assert "january task" in result
    assert "february task" not in result
    assert "4h" in result


def test_monthly_report_no_sessions(tracker):
    """Test monthly report when no sessions exist."""
    result = tracker.report_monthly()

    assert "No sessions recorded" in result


def test_monthly_report_shows_month_name(tracker):
    """Test that monthly report shows month name."""
    tracker.storage.save_completed_session(
        task="test task",
        start_time="2026-01-15T10:00:00",
        end_time="2026-01-15T11:00:00",
        duration_seconds=3600
    )

    result = tracker.report_monthly(month="2026-01")

    assert "January" in result or "2026-01" in result


# ============ TAGS TESTS ============

def test_start_with_single_tag(tracker):
    """Test starting session with a single tag."""
    result = tracker.start("coding", tags=["work"])

    assert "Session started" in result

    active = tracker.storage.load_active_session()
    assert active is not None
    assert active['tags'] == ["work"]


def test_start_with_multiple_tags(tracker):
    """Test starting session with multiple tags."""
    result = tracker.start("meeting", tags=["work", "client"])

    assert "Session started" in result

    active = tracker.storage.load_active_session()
    assert set(active['tags']) == {"work", "client"}


def test_start_without_tags(tracker):
    """Test starting session without tags defaults to empty list."""
    result = tracker.start("coding")

    active = tracker.storage.load_active_session()
    assert active['tags'] == []


def test_stop_saves_tags_to_history(tracker):
    """Test that tags are preserved when session is saved to history."""
    tracker.start("task", tags=["project", "urgent"])
    tracker.stop()

    history = tracker.storage.load_history()
    assert len(history) == 1
    assert set(history[0]['tags']) == {"project", "urgent"}


def test_report_filter_by_tag(tracker):
    """Test filtering report by tag."""
    today = datetime.now().date().isoformat()

    tracker.storage.save_completed_session(
        task="work task",
        start_time=f"{today}T09:00:00",
        end_time=f"{today}T12:00:00",
        duration_seconds=10800,
        tags=["work"]
    )
    tracker.storage.save_completed_session(
        task="personal task",
        start_time=f"{today}T14:00:00",
        end_time=f"{today}T15:00:00",
        duration_seconds=3600,
        tags=["personal"]
    )

    result = tracker.report(tag="work")

    assert "work task" in result
    assert "personal task" not in result


def test_export_filter_by_tag(tracker, tmp_path):
    """Test exporting sessions filtered by tag."""
    today = datetime.now().date().isoformat()

    tracker.storage.save_completed_session(
        task="client work",
        start_time=f"{today}T09:00:00",
        end_time=f"{today}T12:00:00",
        duration_seconds=10800,
        tags=["client", "billable"]
    )
    tracker.storage.save_completed_session(
        task="internal work",
        start_time=f"{today}T14:00:00",
        end_time=f"{today}T15:00:00",
        duration_seconds=3600,
        tags=["internal"]
    )

    output_file = tmp_path / "tagged_export.csv"
    result = tracker.export_csv(str(output_file), tag="client")

    assert "Exported 1 sessions" in result

    import csv
    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    assert rows[0]['task'] == "client work"
    assert "client" in rows[0]['tags']


def test_status_shows_tags(tracker):
    """Test that status displays tags."""
    tracker.start("coding", tags=["work", "python"])
    result = tracker.status()

    assert "work" in result
    assert "python" in result
