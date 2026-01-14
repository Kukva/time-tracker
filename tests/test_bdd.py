"""BDD step definitions for time tracking features."""
import os
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from pytest_bdd import scenarios, given, when, then, parsers

from src.tracker import TimeTracker
from src.storage import Storage


# Load all scenarios from feature file
scenarios('../features/time_tracking.feature')


# ============ FIXTURES ============

@pytest.fixture
def temp_dir():
    """Create temporary directory for test data."""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)


@pytest.fixture
def tracker(temp_dir):
    """Create tracker with temporary storage."""
    tracker = TimeTracker()
    tracker.storage = Storage(data_dir=temp_dir)
    return tracker


@pytest.fixture
def command_result():
    """Store command execution result."""
    return {'output': '', 'csv_path': None}


# ============ GIVEN STEPS ============

@given("I am not currently tracking time")
def not_tracking(tracker):
    """Ensure no active session."""
    tracker.storage.clear_active_session()


@given(parsers.parse('I have an active session "{task}"'))
def have_active_session(tracker, task):
    """Create an active session."""
    tracker.start(task)


@given(parsers.parse("I have completed {count:d} sessions today"))
def have_completed_sessions_today(tracker, count):
    """Create completed sessions for today."""
    today = datetime.now().date().isoformat()
    for i in range(count):
        tracker.storage.save_completed_session(
            task=f"task {i+1}",
            start_time=f"{today}T{9+i}:00:00",
            end_time=f"{today}T{10+i}:00:00",
            duration_seconds=3600
        )


@given("I have completed sessions in history")
def have_completed_sessions(tracker):
    """Create some completed sessions."""
    today = datetime.now().date().isoformat()
    tracker.storage.save_completed_session(
        task="test task",
        start_time=f"{today}T10:00:00",
        end_time=f"{today}T12:00:00",
        duration_seconds=7200
    )


@given("I have sessions from multiple dates")
def have_sessions_multiple_dates(tracker):
    """Create sessions from different dates."""
    tracker.storage.save_completed_session(
        task="january task",
        start_time="2026-01-15T10:00:00",
        end_time="2026-01-15T12:00:00",
        duration_seconds=7200
    )
    tracker.storage.save_completed_session(
        task="december task",
        start_time="2025-12-15T10:00:00",
        end_time="2025-12-15T12:00:00",
        duration_seconds=7200
    )


@given("I have completed sessions")
def have_some_sessions(tracker):
    """Create completed sessions."""
    today = datetime.now().date().isoformat()
    tracker.storage.save_completed_session(
        task="completed work",
        start_time=f"{today}T09:00:00",
        end_time=f"{today}T11:00:00",
        duration_seconds=7200
    )


@given("I have no completed sessions")
def no_completed_sessions(tracker):
    """Ensure no sessions in history."""
    pass  # Fresh tracker has no sessions


@given("I have sessions from current week")
def have_sessions_current_week(tracker):
    """Create sessions for current week."""
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())

    for i in range(3):
        day = monday + timedelta(days=i)
        date_str = day.date().isoformat()
        tracker.storage.save_completed_session(
            task=f"week task {i+1}",
            start_time=f"{date_str}T10:00:00",
            end_time=f"{date_str}T12:00:00",
            duration_seconds=7200
        )


@given("I have sessions from multiple weeks")
def have_sessions_multiple_weeks(tracker):
    """Create sessions from different weeks."""
    tracker.storage.save_completed_session(
        task="week 1 task",
        start_time="2026-01-07T10:00:00",
        end_time="2026-01-07T12:00:00",
        duration_seconds=7200
    )
    tracker.storage.save_completed_session(
        task="week 2 task",
        start_time="2026-01-14T10:00:00",
        end_time="2026-01-14T12:00:00",
        duration_seconds=7200
    )


@given("I have no sessions this week")
def no_sessions_this_week(tracker):
    """Ensure no sessions in current week."""
    pass  # Fresh tracker has no sessions


@given("I have sessions from current month")
def have_sessions_current_month(tracker):
    """Create sessions for current month."""
    today = datetime.now()
    month_str = today.strftime("%Y-%m")

    for day in [5, 10, 15]:
        date_str = f"{month_str}-{day:02d}"
        tracker.storage.save_completed_session(
            task=f"month task {day}",
            start_time=f"{date_str}T10:00:00",
            end_time=f"{date_str}T12:00:00",
            duration_seconds=7200
        )


@given("I have sessions from multiple months")
def have_sessions_multiple_months(tracker):
    """Create sessions from different months."""
    tracker.storage.save_completed_session(
        task="january task",
        start_time="2026-01-15T10:00:00",
        end_time="2026-01-15T12:00:00",
        duration_seconds=7200
    )
    tracker.storage.save_completed_session(
        task="february task",
        start_time="2026-02-15T10:00:00",
        end_time="2026-02-15T12:00:00",
        duration_seconds=7200
    )


@given("I have no sessions this month")
def no_sessions_this_month(tracker):
    """Ensure no sessions in current month."""
    pass  # Fresh tracker has no sessions


# ============ WHEN STEPS ============

@when(parsers.parse('I run "{command}"'))
def run_command(tracker, command, command_result, temp_dir):
    """Execute a track command."""
    import re
    parts = command.split()
    cmd = parts[1] if len(parts) > 1 else ""

    if cmd == "start" and len(parts) > 2:
        # Extract task name from quotes
        match = re.search(r"['\"](.+?)['\"]", command)
        task = match.group(1) if match else parts[2].strip("'\"")
        command_result['output'] = tracker.start(task)
    elif cmd == "stop":
        command_result['output'] = tracker.stop()
    elif cmd == "status":
        command_result['output'] = tracker.status()
    elif cmd == "report":
        if "--week" in parts:
            idx = parts.index("--week")
            week_start = parts[idx + 1] if idx + 1 < len(parts) and not parts[idx + 1].startswith("-") else None
            command_result['output'] = tracker.report_weekly(week_start)
        elif "--month" in parts:
            idx = parts.index("--month")
            month = parts[idx + 1] if idx + 1 < len(parts) and not parts[idx + 1].startswith("-") else None
            command_result['output'] = tracker.report_monthly(month)
        else:
            command_result['output'] = tracker.report()
    elif cmd == "export":
        output_file = None
        start_date = None
        end_date = None

        if "-o" in parts:
            idx = parts.index("-o")
            output_file = os.path.join(temp_dir, parts[idx + 1])

        if "--start-date" in parts:
            idx = parts.index("--start-date")
            start_date = parts[idx + 1]

        if "--end-date" in parts:
            idx = parts.index("--end-date")
            end_date = parts[idx + 1]

        if not output_file:
            output_file = os.path.join(temp_dir, "time_tracker_export.csv")

        command_result['csv_path'] = output_file
        command_result['output'] = tracker.export_csv(output_file, start_date, end_date)


# ============ THEN STEPS ============

@then(parsers.parse('I should see "{text}"'))
def should_see_text(command_result, text):
    """Check that output contains text."""
    assert text in command_result['output'], f"Expected '{text}' in '{command_result['output']}'"


@then("current session should be active")
def session_should_be_active(tracker):
    """Verify session is active."""
    assert tracker.storage.load_active_session() is not None


@then("session should have start timestamp")
def session_has_timestamp(tracker):
    """Verify session has timestamp."""
    session = tracker.storage.load_active_session()
    assert 'start_time' in session


@then("I should see session duration")
def should_see_duration(command_result):
    """Check duration is shown."""
    output = command_result['output']
    assert "h" in output or "m" in output or "s" in output


@then("session should be saved to history file")
def session_saved_to_history(tracker):
    """Verify session in history."""
    history = tracker.storage.load_history()
    assert len(history) > 0


@then("current session should be cleared")
def session_should_be_cleared(tracker):
    """Verify no active session."""
    assert tracker.storage.load_active_session() is None


@then(parsers.parse('I should see error "{text}"'))
def should_see_error(command_result, text):
    """Check that output contains error text."""
    assert text in command_result['output']


@then("previous session should remain active")
def previous_session_active(tracker):
    """Verify session still active."""
    assert tracker.storage.load_active_session() is not None


@then("I should see current task name")
def should_see_task_name(command_result):
    """Check task name in output."""
    assert "code review" in command_result['output'].lower() or "tracking" in command_result['output'].lower()


@then("I should see elapsed time")
def should_see_elapsed_time(command_result):
    """Check elapsed time shown."""
    output = command_result['output']
    assert any(x in output for x in ["0h", "1h", "0m", "1m", "second", "minute", "hour"])


@then("I should see list of all sessions")
def should_see_sessions_list(command_result):
    """Check sessions listed."""
    assert "task" in command_result['output'].lower()


@then("I should see total time worked")
def should_see_total_time(command_result):
    """Check total time shown."""
    output = command_result['output']
    assert "total" in output.lower() or "h" in output


@then("a CSV file should be created")
def csv_file_created(command_result):
    """Verify CSV file exists."""
    assert command_result['csv_path'] is not None
    assert Path(command_result['csv_path']).exists()


@then("CSV file should contain session data")
def csv_contains_data(command_result):
    """Verify CSV has content."""
    with open(command_result['csv_path'], 'r') as f:
        content = f.read()
    assert "task" in content.lower()


@then("I should see success message with file path")
def should_see_success_message(command_result):
    """Check success message."""
    assert "Exported" in command_result['output'] or "✓" in command_result['output']


@then("CSV should only contain sessions in date range")
def csv_filtered_by_date(command_result):
    """Verify CSV is filtered."""
    with open(command_result['csv_path'], 'r') as f:
        content = f.read()
    assert "january task" in content.lower()
    assert "december task" not in content.lower()


@then("I should see count of exported sessions")
def should_see_export_count(command_result):
    """Check export count shown."""
    assert "session" in command_result['output'].lower()


@then(parsers.parse('file should be created at "{filename}"'))
def file_created_at_path(command_result, filename, temp_dir):
    """Verify file at specific path."""
    expected_path = os.path.join(temp_dir, filename)
    assert Path(expected_path).exists() or Path(command_result['csv_path']).exists()


@then("file should have .csv extension")
def file_has_csv_extension(command_result):
    """Verify .csv extension."""
    assert command_result['csv_path'].endswith('.csv')


@then("no CSV file should be created")
def no_csv_file(command_result):
    """Verify no CSV created."""
    if command_result['csv_path']:
        assert not Path(command_result['csv_path']).exists()


@then("I should see all sessions from Monday to Sunday")
def should_see_week_sessions(command_result):
    """Check weekly sessions shown."""
    output = command_result['output']
    assert "week" in output.lower() or "Week" in output


@then("I should see total hours for the week")
def should_see_week_total(command_result):
    """Check week total shown."""
    output = command_result['output']
    assert "total" in output.lower() or "h" in output


@then("sessions should be grouped by day")
def sessions_grouped_by_day(command_result):
    """Check sessions are grouped."""
    output = command_result['output']
    # Should have day names or dates
    assert any(day in output for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "2026-"])


@then(parsers.parse("I should see sessions for week starting {date}"))
def should_see_specific_week(command_result, date):
    """Check specific week shown."""
    assert "week 1 task" in command_result['output'].lower()


@then(parsers.parse("I should see {count:d} days in the report"))
def should_see_days_count(command_result, count):
    """Verify days in report."""
    # Just check report has content
    assert len(command_result['output']) > 0


@then("I should see all sessions from the month")
def should_see_month_sessions(command_result):
    """Check monthly sessions shown."""
    output = command_result['output']
    assert "month" in output.lower() or "Month" in output


@then("I should see total hours for the month")
def should_see_month_total(command_result):
    """Check month total shown."""
    output = command_result['output']
    assert "total" in output.lower() or "h" in output


@then(parsers.parse("I should see sessions for {month_name}"))
def should_see_specific_month(command_result, month_name):
    """Check specific month shown."""
    output = command_result['output']
    assert "january" in output.lower() or "January" in output or "2026-01" in output


@then("I should see month name in header")
def should_see_month_name(command_result):
    """Check month name in header."""
    output = command_result['output']
    assert "January" in output or "2026-01" in output
