"""Telegram bot for Time Tracker with reminders."""
import json
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Tuple

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

from .tracker import TimeTracker
from .storage import Storage

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Default config path
DEFAULT_CONFIG_DIR = Path.home() / ".timetracker"


def load_bot_config(config_dir: Optional[str] = None) -> Optional[Dict]:
    """Load bot configuration from file."""
    if config_dir:
        config_path = Path(config_dir) / "telegram.json"
    else:
        config_path = DEFAULT_CONFIG_DIR / "telegram.json"

    if not config_path.exists():
        return None

    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def save_bot_config(config: Dict, config_dir: Optional[str] = None) -> None:
    """Save bot configuration to file."""
    if config_dir:
        config_path = Path(config_dir) / "telegram.json"
    else:
        config_path = DEFAULT_CONFIG_DIR / "telegram.json"

    config_path.parent.mkdir(exist_ok=True)

    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)


def format_elapsed_time(seconds: int) -> str:
    """Format seconds into readable string."""
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def format_session_message(session: Dict) -> str:
    """Format session info for Telegram message."""
    task = session.get('task', 'Unknown')
    duration = session.get('duration_seconds', 0)
    duration_str = format_elapsed_time(duration)

    start = session.get('start_time', '')[:16].replace('T', ' ')
    end = session.get('end_time', '')[:16].replace('T', ' ')

    return f"📋 *{task}*\n⏱ {duration_str}\n🕐 {start} → {end}"


def format_status_message(is_tracking: bool, task: Optional[str], elapsed_seconds: int) -> str:
    """Format status message for Telegram."""
    if is_tracking and task:
        elapsed_str = format_elapsed_time(elapsed_seconds)
        return f"🟢 *Currently tracking:*\n\n📋 {task}\n⏱ Elapsed: {elapsed_str}"
    else:
        return "🟡 *Not tracking any task*\n\nUse /start <task> to begin"


# ============ COMMAND HANDLERS ============

async def handle_start_command(task: str, tracker: TimeTracker) -> str:
    """Handle /start command - begin tracking."""
    if not task or not task.strip():
        return "❌ Please provide a task name.\n\nUsage: `/start <task name>`"

    result = tracker.start(task.strip())
    return f"✅ {result}"


async def handle_stop_command(tracker: TimeTracker) -> str:
    """Handle /stop command - stop tracking."""
    active = tracker.storage.load_active_session()

    if not active:
        return "⚠️ Not tracking any task.\n\nUse /start <task> to begin."

    result = tracker.stop()
    return f"⏹ {result}"


async def handle_status_command(tracker: TimeTracker) -> str:
    """Handle /status command - show current status."""
    active = tracker.storage.load_active_session()

    if active:
        task = active['task']
        start_time = datetime.fromisoformat(active['start_time'])
        elapsed = int((datetime.now() - start_time).total_seconds())
        return format_status_message(True, task, elapsed)
    else:
        return format_status_message(False, None, 0)


async def handle_report_command(tracker: TimeTracker) -> str:
    """Handle /report command - show daily report."""
    report = tracker.report()
    return f"📊 *Daily Report*\n\n{report}"


async def handle_help_command() -> str:
    """Handle /help command - show available commands."""
    return """🤖 *Time Tracker Bot Commands*

/start <task> - Start tracking a task
/stop - Stop current tracking
/status - Show current status
/report - Today's report
/week - Weekly report
/month - Monthly report
/help - Show this help

⏰ *Reminders:*
Bot will remind you if tracking >4 hours.
Daily summary at configured time."""


# ============ REMINDER FUNCTIONS ============

def check_needs_reminder(tracker: TimeTracker, max_hours: int = 4) -> Tuple[bool, str]:
    """Check if user needs a reminder about long session."""
    active = tracker.storage.load_active_session()

    if not active:
        return False, ""

    start_time = datetime.fromisoformat(active['start_time'])
    elapsed = datetime.now() - start_time
    elapsed_hours = elapsed.total_seconds() / 3600

    if elapsed_hours >= max_hours:
        task = active['task']
        elapsed_str = format_elapsed_time(int(elapsed.total_seconds()))
        message = f"""⚠️ *Long Session Alert!*

You've been tracking "*{task}*" for {elapsed_str}.

Did you forget to stop the timer?

Use /stop to end the session or ignore this message if you're still working."""
        return True, message

    return False, ""


def generate_daily_summary(tracker: TimeTracker) -> str:
    """Generate daily summary message."""
    today = datetime.now().date().isoformat()
    history = tracker.storage.load_history()

    # Filter today's sessions
    today_sessions = [
        s for s in history
        if s.get('start_time', '').startswith(today)
    ]

    if not today_sessions:
        return "📊 *Daily Summary*\n\nNo sessions recorded today."

    total_seconds = sum(s.get('duration_seconds', 0) for s in today_sessions)
    total_str = format_elapsed_time(total_seconds)

    lines = ["📊 *Daily Summary*\n"]

    for session in today_sessions:
        task = session.get('task', 'Unknown')
        duration = session.get('duration_seconds', 0)
        duration_str = format_elapsed_time(duration)
        lines.append(f"• {task}: {duration_str}")

    lines.append(f"\n*Total: {total_str}*")

    return "\n".join(lines)


# ============ TELEGRAM HANDLERS ============

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command from Telegram."""
    tracker = TimeTracker()

    # Get task name from arguments
    task = ' '.join(context.args) if context.args else ''

    if not task:
        # If no task, show welcome message
        await update.message.reply_text(
            "👋 *Welcome to Time Tracker Bot!*\n\n"
            "Use `/start <task>` to begin tracking.\n"
            "Example: `/start coding new feature`\n\n"
            "Type /help for all commands.",
            parse_mode='Markdown'
        )
        return

    result = await handle_start_command(task, tracker)
    await update.message.reply_text(result, parse_mode='Markdown')


async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stop command from Telegram."""
    tracker = TimeTracker()
    result = await handle_stop_command(tracker)
    await update.message.reply_text(result, parse_mode='Markdown')


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command from Telegram."""
    tracker = TimeTracker()
    result = await handle_status_command(tracker)
    await update.message.reply_text(result, parse_mode='Markdown')


async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /report command from Telegram."""
    tracker = TimeTracker()
    result = await handle_report_command(tracker)
    await update.message.reply_text(result, parse_mode='Markdown')


async def cmd_week(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /week command from Telegram."""
    tracker = TimeTracker()
    report = tracker.report_weekly()
    await update.message.reply_text(f"📊 *Weekly Report*\n\n{report}", parse_mode='Markdown')


async def cmd_month(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /month command from Telegram."""
    tracker = TimeTracker()
    report = tracker.report_monthly()
    await update.message.reply_text(f"📊 *Monthly Report*\n\n{report}", parse_mode='Markdown')


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command from Telegram."""
    result = await handle_help_command()
    await update.message.reply_text(result, parse_mode='Markdown')


async def reminder_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Job to check for long sessions and send reminders."""
    tracker = TimeTracker()
    config = load_bot_config()

    if not config:
        return

    max_hours = config.get('reminder_hours', 4)
    needs_reminder, message = check_needs_reminder(tracker, max_hours)

    if needs_reminder:
        chat_id = config.get('chat_id')
        if chat_id:
            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown'
            )


async def daily_summary_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Job to send daily summary."""
    tracker = TimeTracker()
    config = load_bot_config()

    if not config:
        return

    chat_id = config.get('chat_id')
    if chat_id:
        summary = generate_daily_summary(tracker)
        await context.bot.send_message(
            chat_id=chat_id,
            text=summary,
            parse_mode='Markdown'
        )


def run_bot(token: str = None) -> None:
    """Run the Telegram bot."""
    if not token:
        config = load_bot_config()
        if not config or 'token' not in config:
            print("❌ No bot token configured.")
            print("Run 'track bot --setup' to configure.")
            return
        token = config['token']

    # Create application
    app = Application.builder().token(token).build()

    # Add command handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("stop", cmd_stop))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("report", cmd_report))
    app.add_handler(CommandHandler("week", cmd_week))
    app.add_handler(CommandHandler("month", cmd_month))
    app.add_handler(CommandHandler("help", cmd_help))

    # Add reminder job (check every 30 minutes)
    job_queue = app.job_queue
    job_queue.run_repeating(reminder_job, interval=1800, first=60)

    print("🤖 Time Tracker Bot started!")
    print("Press Ctrl+C to stop.")

    # Run bot
    app.run_polling(allowed_updates=Update.ALL_TYPES)


def setup_bot() -> None:
    """Interactive bot setup."""
    print("\n🤖 Telegram Bot Setup\n")

    token = input("Enter your bot token (from @BotFather): ").strip()

    if not token:
        print("❌ Token is required.")
        return

    chat_id = input("Enter your Telegram chat ID (optional, press Enter to skip): ").strip()

    config = {
        "token": token,
        "reminder_hours": 4,
        "daily_summary_time": "18:00"
    }

    if chat_id:
        try:
            config["chat_id"] = int(chat_id)
        except ValueError:
            print("⚠️ Invalid chat ID, skipping.")

    save_bot_config(config)

    print("\n✅ Bot configured successfully!")
    print("Run 'track bot' to start the bot.")
    print("\nTo get your chat ID:")
    print("1. Start the bot")
    print("2. Send any message to your bot")
    print("3. The bot will reply with your chat ID")
