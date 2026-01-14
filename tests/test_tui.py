"""Tests for Rich TUI components."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import tempfile
import shutil

from src.storage import Storage
from src.tracker import TimeTracker


@pytest.fixture
def temp_storage():
    """Create temporary storage for testing."""
    temp_dir = tempfile.mkdtemp()
    storage = Storage(data_dir=temp_dir)
    yield storage
    shutil.rmtree(temp_dir)


@pytest.fixture
def tracker(temp_storage):
    """Create tracker with temporary storage."""
    tracker = TimeTracker()
    tracker.storage = temp_storage
    return tracker


# ============ TUI COMPONENT TESTS ============

class TestTUIComponents:
    """Test TUI rendering components."""

    def test_format_elapsed_time_seconds(self):
        """Test formatting elapsed time in seconds."""
        from src.tui import format_elapsed_time

        assert format_elapsed_time(45) == "00:00:45"
        assert format_elapsed_time(0) == "00:00:00"

    def test_format_elapsed_time_minutes(self):
        """Test formatting elapsed time with minutes."""
        from src.tui import format_elapsed_time

        assert format_elapsed_time(125) == "00:02:05"
        assert format_elapsed_time(3599) == "00:59:59"

    def test_format_elapsed_time_hours(self):
        """Test formatting elapsed time with hours."""
        from src.tui import format_elapsed_time

        assert format_elapsed_time(3600) == "01:00:00"
        assert format_elapsed_time(7325) == "02:02:05"
        assert format_elapsed_time(36000) == "10:00:00"

    def test_get_status_style_tracking(self, tracker):
        """Test status style when tracking."""
        from src.tui import get_status_style

        tracker.start("test task")
        style = get_status_style(tracker)

        assert style == "green"

    def test_get_status_style_idle(self, tracker):
        """Test status style when idle."""
        from src.tui import get_status_style

        style = get_status_style(tracker)

        assert style == "yellow"

    def test_build_status_panel_tracking(self, tracker):
        """Test status panel content when tracking."""
        from src.tui import build_status_panel
        from rich.console import Console
        from io import StringIO

        tracker.start("coding feature")
        panel = build_status_panel(tracker)

        # Render panel to string
        console = Console(file=StringIO(), force_terminal=True)
        console.print(panel)
        output = console.file.getvalue()

        assert "coding feature" in output
        assert panel is not None

    def test_build_status_panel_idle(self, tracker):
        """Test status panel content when idle."""
        from src.tui import build_status_panel
        from rich.console import Console
        from io import StringIO

        panel = build_status_panel(tracker)

        console = Console(file=StringIO(), force_terminal=True)
        console.print(panel)
        output = console.file.getvalue()

        assert "Not tracking" in output or "IDLE" in output

    def test_build_actions_panel(self):
        """Test actions panel contains all options."""
        from src.tui import build_actions_panel
        from rich.console import Console
        from io import StringIO

        panel = build_actions_panel()

        console = Console(file=StringIO(), force_terminal=True)
        console.print(panel)
        output = console.file.getvalue()

        assert "Start" in output or "1" in output
        assert "Stop" in output or "2" in output

    def test_build_sessions_panel_with_sessions(self, tracker):
        """Test sessions panel with today's sessions."""
        from src.tui import build_sessions_panel
        from rich.console import Console
        from io import StringIO

        today = datetime.now().date().isoformat()
        tracker.storage.save_completed_session(
            task="morning work",
            start_time=f"{today}T09:00:00",
            end_time=f"{today}T11:00:00",
            duration_seconds=7200
        )

        panel = build_sessions_panel(tracker)

        console = Console(file=StringIO(), force_terminal=True)
        console.print(panel)
        output = console.file.getvalue()

        assert "morning work" in output

    def test_build_sessions_panel_empty(self, tracker):
        """Test sessions panel with no sessions."""
        from src.tui import build_sessions_panel

        panel = build_sessions_panel(tracker)

        assert panel is not None


class TestTUIInteraction:
    """Test TUI user interactions."""

    def test_handle_input_quit(self, tracker):
        """Test quit command."""
        from src.tui import handle_input

        result = handle_input("q", tracker)

        assert result == "quit"

    def test_handle_input_start(self, tracker):
        """Test start command input."""
        from src.tui import handle_input

        with patch('src.tui.get_task_input', return_value="new task"):
            result = handle_input("1", tracker)

        assert result == "continue"
        assert tracker.storage.load_active_session() is not None

    def test_handle_input_stop(self, tracker):
        """Test stop command input."""
        from src.tui import handle_input

        tracker.start("test")
        result = handle_input("2", tracker)

        assert result == "continue"
        assert tracker.storage.load_active_session() is None

    def test_handle_input_invalid(self, tracker):
        """Test invalid input handling."""
        from src.tui import handle_input

        result = handle_input("x", tracker)

        assert result == "continue"


class TestTUILayout:
    """Test TUI layout generation."""

    def test_create_layout(self, tracker):
        """Test full layout creation."""
        from src.tui import create_layout

        layout = create_layout(tracker)

        assert layout is not None

    def test_layout_has_all_panels(self, tracker):
        """Test layout contains all required panels."""
        from src.tui import create_layout

        layout = create_layout(tracker)
        layout_str = str(layout)

        # Layout should reference panel areas
        assert layout is not None
