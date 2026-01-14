"""Tests for Telegram bot functionality."""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import tempfile
import shutil
import json

from src.storage import Storage
from src.tracker import TimeTracker


@pytest.fixture
def temp_storage():
    """Create temporary storage for testing."""
    temp_dir = tempfile.mkdtemp()
    storage = Storage(data_dir=temp_dir)
    yield storage, temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def tracker(temp_storage):
    """Create tracker with temporary storage."""
    storage, temp_dir = temp_storage
    tracker = TimeTracker()
    tracker.storage = storage
    return tracker, temp_dir


# ============ BOT CONFIG TESTS ============

class TestBotConfig:
    """Test bot configuration handling."""

    def test_load_config_exists(self, temp_storage):
        """Test loading existing config."""
        from src.telegram_bot import load_bot_config

        storage, temp_dir = temp_storage
        config_path = f"{temp_dir}/telegram.json"

        config = {
            "token": "test_token_123",
            "chat_id": 12345,
            "reminder_hours": 4,
            "daily_summary_time": "18:00"
        }
        with open(config_path, 'w') as f:
            json.dump(config, f)

        loaded = load_bot_config(temp_dir)

        assert loaded["token"] == "test_token_123"
        assert loaded["chat_id"] == 12345

    def test_load_config_not_exists(self, temp_storage):
        """Test loading when config doesn't exist."""
        from src.telegram_bot import load_bot_config

        storage, temp_dir = temp_storage
        loaded = load_bot_config(temp_dir)

        assert loaded is None

    def test_save_config(self, temp_storage):
        """Test saving config."""
        from src.telegram_bot import save_bot_config

        storage, temp_dir = temp_storage
        config = {
            "token": "new_token",
            "chat_id": 99999
        }

        save_bot_config(config, temp_dir)

        with open(f"{temp_dir}/telegram.json", 'r') as f:
            saved = json.load(f)

        assert saved["token"] == "new_token"


# ============ BOT COMMAND TESTS ============

class TestBotCommands:
    """Test bot command handlers."""

    @pytest.mark.asyncio
    async def test_start_command_begins_tracking(self, tracker):
        """Test /start command starts tracking."""
        from src.telegram_bot import handle_start_command

        tracker_obj, temp_dir = tracker

        result = await handle_start_command("coding feature", tracker_obj)

        assert "started" in result.lower()
        assert tracker_obj.storage.load_active_session() is not None

    @pytest.mark.asyncio
    async def test_start_command_no_task(self, tracker):
        """Test /start without task name."""
        from src.telegram_bot import handle_start_command

        tracker_obj, temp_dir = tracker

        result = await handle_start_command("", tracker_obj)

        assert "provide" in result.lower() or "task" in result.lower()

    @pytest.mark.asyncio
    async def test_stop_command_stops_tracking(self, tracker):
        """Test /stop command stops tracking."""
        from src.telegram_bot import handle_stop_command

        tracker_obj, temp_dir = tracker
        tracker_obj.start("test task")

        result = await handle_stop_command(tracker_obj)

        assert tracker_obj.storage.load_active_session() is None
        assert "stopped" in result.lower() or "session" in result.lower()

    @pytest.mark.asyncio
    async def test_stop_command_not_tracking(self, tracker):
        """Test /stop when not tracking."""
        from src.telegram_bot import handle_stop_command

        tracker_obj, temp_dir = tracker

        result = await handle_stop_command(tracker_obj)

        assert "not tracking" in result.lower() or "no active" in result.lower()

    @pytest.mark.asyncio
    async def test_status_command_tracking(self, tracker):
        """Test /status when tracking."""
        from src.telegram_bot import handle_status_command

        tracker_obj, temp_dir = tracker
        tracker_obj.start("status test")

        result = await handle_status_command(tracker_obj)

        assert "status test" in result.lower()

    @pytest.mark.asyncio
    async def test_status_command_idle(self, tracker):
        """Test /status when idle."""
        from src.telegram_bot import handle_status_command

        tracker_obj, temp_dir = tracker

        result = await handle_status_command(tracker_obj)

        assert "not tracking" in result.lower() or "idle" in result.lower()

    @pytest.mark.asyncio
    async def test_report_command(self, tracker):
        """Test /report command."""
        from src.telegram_bot import handle_report_command

        tracker_obj, temp_dir = tracker
        today = datetime.now().date().isoformat()
        tracker_obj.storage.save_completed_session(
            task="report test",
            start_time=f"{today}T10:00:00",
            end_time=f"{today}T12:00:00",
            duration_seconds=7200
        )

        result = await handle_report_command(tracker_obj)

        assert "report test" in result.lower() or "2h" in result

    @pytest.mark.asyncio
    async def test_help_command(self):
        """Test /help command."""
        from src.telegram_bot import handle_help_command

        result = await handle_help_command()

        assert "/start" in result
        assert "/stop" in result
        assert "/status" in result


# ============ REMINDER TESTS ============

class TestReminders:
    """Test reminder functionality."""

    def test_check_long_session_needs_reminder(self, tracker):
        """Test detecting long session that needs reminder."""
        from src.telegram_bot import check_needs_reminder

        tracker_obj, temp_dir = tracker

        # Create session started 5 hours ago
        start_time = datetime.now() - timedelta(hours=5)
        tracker_obj.storage.save_active_session(
            "long task",
            start_time.isoformat()
        )

        needs_reminder, message = check_needs_reminder(tracker_obj, max_hours=4)

        assert needs_reminder is True
        assert "long task" in message or "4" in message

    def test_check_short_session_no_reminder(self, tracker):
        """Test short session doesn't need reminder."""
        from src.telegram_bot import check_needs_reminder

        tracker_obj, temp_dir = tracker

        # Create session started 1 hour ago
        start_time = datetime.now() - timedelta(hours=1)
        tracker_obj.storage.save_active_session(
            "short task",
            start_time.isoformat()
        )

        needs_reminder, message = check_needs_reminder(tracker_obj, max_hours=4)

        assert needs_reminder is False

    def test_check_no_session_no_reminder(self, tracker):
        """Test no reminder when not tracking."""
        from src.telegram_bot import check_needs_reminder

        tracker_obj, temp_dir = tracker

        needs_reminder, message = check_needs_reminder(tracker_obj, max_hours=4)

        assert needs_reminder is False


class TestDailySummary:
    """Test daily summary functionality."""

    def test_generate_daily_summary_with_sessions(self, tracker):
        """Test daily summary generation."""
        from src.telegram_bot import generate_daily_summary

        tracker_obj, temp_dir = tracker
        today = datetime.now().date().isoformat()

        tracker_obj.storage.save_completed_session(
            task="morning work",
            start_time=f"{today}T09:00:00",
            end_time=f"{today}T12:00:00",
            duration_seconds=10800
        )
        tracker_obj.storage.save_completed_session(
            task="afternoon work",
            start_time=f"{today}T14:00:00",
            end_time=f"{today}T17:00:00",
            duration_seconds=10800
        )

        summary = generate_daily_summary(tracker_obj)

        assert "morning work" in summary or "6h" in summary
        assert summary is not None

    def test_generate_daily_summary_no_sessions(self, tracker):
        """Test daily summary with no sessions."""
        from src.telegram_bot import generate_daily_summary

        tracker_obj, temp_dir = tracker

        summary = generate_daily_summary(tracker_obj)

        assert "no sessions" in summary.lower() or summary is not None


# ============ MESSAGE FORMATTING TESTS ============

class TestMessageFormatting:
    """Test message formatting for Telegram."""

    def test_format_session_message(self):
        """Test formatting session info for Telegram."""
        from src.telegram_bot import format_session_message

        session = {
            "task": "test task",
            "start_time": "2026-01-14T10:00:00",
            "end_time": "2026-01-14T12:00:00",
            "duration_seconds": 7200
        }

        message = format_session_message(session)

        assert "test task" in message
        assert "2h" in message or "2 h" in message

    def test_format_status_message_tracking(self):
        """Test status message when tracking."""
        from src.telegram_bot import format_status_message

        message = format_status_message(
            is_tracking=True,
            task="coding",
            elapsed_seconds=3661
        )

        assert "coding" in message
        assert "1h" in message or "01:" in message

    def test_format_status_message_idle(self):
        """Test status message when idle."""
        from src.telegram_bot import format_status_message

        message = format_status_message(
            is_tracking=False,
            task=None,
            elapsed_seconds=0
        )

        assert "not tracking" in message.lower() or "idle" in message.lower()
