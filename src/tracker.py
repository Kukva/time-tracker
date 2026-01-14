import click
import csv
from datetime import datetime, timedelta
from typing import Optional, List
from pathlib import Path
from .storage import Storage

class TimeTracker:
    """Main time tracking logic."""
    
    def __init__(self):
        self.storage = Storage()
    
    def _validate_task_name(self, task: str) -> Optional[str]:
        """
        Validate task name.
        Returns error message if invalid, None if valid.
        """
        # Check for empty or whitespace-only
        if not task or not task.strip():
            return "❌ Task name cannot be empty"
        
        # Check length
        if len(task) > 100:
            return f"❌ Task name too long ({len(task)} chars, max 100)"
        
        # Check for problematic characters
        forbidden_chars = ['\n', '\r', '\t']
        for char in forbidden_chars:
            if char in task:
                return f"❌ Task name contains invalid character: {repr(char)}"
        
        return None  # Valid
    
    def start(self, task: str, tags: List[str] = None) -> str:
        """Start tracking a new task."""
        # Validate task name
        validation_error = self._validate_task_name(task)
        if validation_error:
            return validation_error

        # Trim whitespace
        task = task.strip()
        tags = tags or []

        active = self.storage.load_active_session()

        if active:
            return f"❌ Already tracking: {active['task']}\nStop current session first."

        start_time = datetime.now().isoformat()
        self.storage.save_active_session(task, start_time, tags)

        tag_str = f" [{', '.join(tags)}]" if tags else ""
        return f"✓ Session started: {task}{tag_str}"
    
    def stop(self) -> str:
        """Stop the current tracking session."""
        active = self.storage.load_active_session()
        
        if not active:
            return "❌ No active session to stop"
        
        try:
            start_time = datetime.fromisoformat(active['start_time'])
        except (ValueError, KeyError) as e:
            return "❌ Error: Active session has invalid data. Clearing it."
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Sanity check: duration should be positive and reasonable
        if duration.total_seconds() < 0:
            return "❌ Error: Invalid session duration (negative time)"
        
        if duration.total_seconds() > 86400 * 7:  # More than 7 days
            return "⚠️  Warning: Session longer than 7 days. Did you forget to stop? Session not saved."
        
        tags = active.get('tags', [])
        self.storage.save_completed_session(
            task=active['task'],
            start_time=active['start_time'],
            end_time=end_time.isoformat(),
            duration_seconds=int(duration.total_seconds()),
            tags=tags
        )

        self.storage.clear_active_session()

        hours, remainder = divmod(int(duration.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)

        tag_str = f" [{', '.join(tags)}]" if tags else ""
        return f"✓ Session stopped: {active['task']}{tag_str}\nDuration: {hours}h {minutes}m"
    
    def status(self) -> str:
        """Show current tracking status."""
        active = self.storage.load_active_session()

        if not active:
            return "No active session"

        try:
            start_time = datetime.fromisoformat(active['start_time'])
        except (ValueError, KeyError):
            return "❌ Error: Active session has invalid data"

        elapsed = datetime.now() - start_time

        hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)

        tags = active.get('tags', [])
        tag_str = f"\nTags: {', '.join(tags)}" if tags else ""
        return f"📍 Tracking: {active['task']}\nElapsed: {hours}h {minutes}m{tag_str}"
    
    def report(self, date: Optional[str] = None, tag: Optional[str] = None) -> str:
        """Generate report for specified date (defaults to today)."""
        history = self.storage.load_history()

        if not history:
            return "No sessions recorded yet"

        # Filter by date if specified
        target_date = date if date else datetime.now().date().isoformat()

        filtered_sessions = []
        for session in history:
            try:
                if session['start_time'].startswith(target_date):
                    # Filter by tag if specified
                    if tag:
                        session_tags = session.get('tags', [])
                        if tag not in session_tags:
                            continue
                    filtered_sessions.append(session)
            except (KeyError, TypeError):
                # Skip malformed sessions
                continue

        if not filtered_sessions:
            tag_info = f" with tag '{tag}'" if tag else ""
            return f"No sessions on {target_date}{tag_info}"

        total_seconds = sum(s.get('duration_seconds', 0) for s in filtered_sessions)
        total_hours, remainder = divmod(total_seconds, 3600)
        total_minutes, _ = divmod(remainder, 60)

        tag_info = f" [tag: {tag}]" if tag else ""
        output = [f"📊 Report for {target_date}{tag_info}", "=" * 40]

        for session in filtered_sessions:
            try:
                start = datetime.fromisoformat(session['start_time'])
                hours, remainder = divmod(session['duration_seconds'], 3600)
                minutes, _ = divmod(remainder, 60)

                session_tags = session.get('tags', [])
                tag_str = f" [{', '.join(session_tags)}]" if session_tags else ""
                output.append(
                    f"{start.strftime('%H:%M')} | {session['task']}{tag_str} | {hours}h {minutes}m"
                )
            except (ValueError, KeyError, TypeError):
                # Skip malformed entries
                output.append(f"[Corrupted entry - skipped]")
                continue

        output.append("=" * 40)
        output.append(f"Total: {total_hours}h {total_minutes}m")

        return "\n".join(output)

    def export_csv(self, output_file: Optional[str] = None,
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None,
                   tag: Optional[str] = None) -> str:
        """
        Export sessions to CSV file.

        Args:
            output_file: Path to output CSV file (defaults to ./time_tracker_export.csv)
            start_date: Filter sessions from this date (YYYY-MM-DD format)
            end_date: Filter sessions until this date (YYYY-MM-DD format)
            tag: Filter sessions by tag

        Returns:
            Success/error message
        """
        history = self.storage.load_history()

        if not history:
            return "❌ No sessions to export"

        # Filter by date range and tag if specified
        filtered_sessions = []
        for session in history:
            try:
                session_date = session['start_time'][:10]  # Extract YYYY-MM-DD

                # Check date range
                if start_date and session_date < start_date:
                    continue
                if end_date and session_date > end_date:
                    continue

                # Check tag filter
                if tag:
                    session_tags = session.get('tags', [])
                    if tag not in session_tags:
                        continue

                filtered_sessions.append(session)
            except (KeyError, TypeError, IndexError):
                # Skip malformed sessions
                continue

        if not filtered_sessions:
            return "❌ No sessions found in specified date range"

        # Set default output file
        if not output_file:
            output_file = "time_tracker_export.csv"

        # Ensure .csv extension
        output_path = Path(output_file)
        if output_path.suffix.lower() != '.csv':
            output_path = output_path.with_suffix('.csv')

        try:
            # Write CSV
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'task', 'start_time', 'end_time', 'duration_hours', 'duration_minutes', 'tags'
                ])
                writer.writeheader()

                for session in filtered_sessions:
                    try:
                        hours, remainder = divmod(session['duration_seconds'], 3600)
                        minutes, _ = divmod(remainder, 60)
                        session_tags = session.get('tags', [])

                        writer.writerow({
                            'task': session['task'],
                            'start_time': session['start_time'],
                            'end_time': session['end_time'],
                            'duration_hours': hours,
                            'duration_minutes': minutes,
                            'tags': ', '.join(session_tags)
                        })
                    except (KeyError, TypeError):
                        # Skip malformed entries
                        continue

            return f"✓ Exported {len(filtered_sessions)} sessions to {output_path.absolute()}"

        except (IOError, PermissionError) as e:
            return f"❌ Error writing CSV file: {e}"

    def report_weekly(self, week_start: Optional[str] = None) -> str:
        """
        Show weekly report.

        Args:
            week_start: Start date of week in YYYY-MM-DD format (defaults to current week)

        Returns:
            Formatted weekly report
        """
        from collections import defaultdict

        history = self.storage.load_history()

        if not history:
            return "No sessions recorded for this week."

        # Determine week range
        if week_start:
            start_date = datetime.fromisoformat(week_start).date()
        else:
            today = datetime.now().date()
            start_date = today - timedelta(days=today.weekday())  # Monday

        end_date = start_date + timedelta(days=6)  # Sunday

        # Filter sessions for the week
        weekly_sessions = defaultdict(list)
        for session in history:
            try:
                session_date = datetime.fromisoformat(session['start_time'][:10]).date()

                if start_date <= session_date <= end_date:
                    weekly_sessions[session_date].append(session)
            except (KeyError, ValueError, TypeError):
                continue

        if not weekly_sessions:
            return "No sessions recorded for this week."

        # Build report
        output = []
        output.append("=" * 40)
        output.append(f"Week: {start_date} to {end_date}")
        output.append("=" * 40)

        total_seconds = 0
        for date in sorted(weekly_sessions.keys()):
            day_name = date.strftime("%A")
            output.append(f"\n{day_name}, {date}:")

            day_seconds = 0
            for session in weekly_sessions[date]:
                try:
                    duration = session['duration_seconds']
                    hours, remainder = divmod(duration, 3600)
                    minutes, _ = divmod(remainder, 60)

                    task = session['task']
                    output.append(f"  {task}: {hours}h {minutes}m")

                    day_seconds += duration
                    total_seconds += duration
                except (KeyError, TypeError):
                    continue

            # Day total
            day_hours, day_remainder = divmod(day_seconds, 3600)
            day_minutes, _ = divmod(day_remainder, 60)
            output.append(f"  Day total: {day_hours}h {day_minutes}m")

        # Week total
        total_hours, total_remainder = divmod(total_seconds, 3600)
        total_minutes, _ = divmod(total_remainder, 60)
        output.append("=" * 40)
        output.append(f"Week Total: {total_hours}h {total_minutes}m")

        return "\n".join(output)

    def report_monthly(self, month: Optional[str] = None) -> str:
        """
        Show monthly report.

        Args:
            month: Month in YYYY-MM format (defaults to current month)

        Returns:
            Formatted monthly report
        """
        from collections import defaultdict
        import calendar

        history = self.storage.load_history()

        if not history:
            return "No sessions recorded for this month."

        # Determine month range
        if month:
            year, month_num = map(int, month.split('-'))
            start_date = datetime(year, month_num, 1).date()
        else:
            today = datetime.now().date()
            start_date = datetime(today.year, today.month, 1).date()

        # Calculate last day of month
        last_day = calendar.monthrange(start_date.year, start_date.month)[1]
        end_date = datetime(start_date.year, start_date.month, last_day).date()

        # Filter sessions for the month
        monthly_sessions = defaultdict(list)
        for session in history:
            try:
                session_date = datetime.fromisoformat(session['start_time'][:10]).date()

                if start_date <= session_date <= end_date:
                    monthly_sessions[session_date].append(session)
            except (KeyError, ValueError, TypeError):
                continue

        if not monthly_sessions:
            return "No sessions recorded for this month."

        # Build report
        month_name = start_date.strftime("%B %Y")
        output = []
        output.append("=" * 40)
        output.append(f"Month: {month_name}")
        output.append("=" * 40)

        total_seconds = 0
        for date in sorted(monthly_sessions.keys()):
            day_name = date.strftime("%A")
            output.append(f"\n{day_name}, {date}:")

            day_seconds = 0
            for session in monthly_sessions[date]:
                try:
                    duration = session['duration_seconds']
                    hours, remainder = divmod(duration, 3600)
                    minutes, _ = divmod(remainder, 60)

                    task = session['task']
                    output.append(f"  {task}: {hours}h {minutes}m")

                    day_seconds += duration
                    total_seconds += duration
                except (KeyError, TypeError):
                    continue

            # Day total
            day_hours, day_remainder = divmod(day_seconds, 3600)
            day_minutes, _ = divmod(day_remainder, 60)
            output.append(f"  Day total: {day_hours}h {day_minutes}m")

        # Month total
        total_hours, total_remainder = divmod(total_seconds, 3600)
        total_minutes, _ = divmod(total_remainder, 60)
        output.append("=" * 40)
        output.append(f"Month Total: {total_hours}h {total_minutes}m")

        return "\n".join(output)

    # ============ POMODORO METHODS ============

    def pomodoro_start(self, task: str, duration: int = 25, tags: List[str] = None) -> str:
        """
        Start a pomodoro session.

        Args:
            task: Task name
            duration: Duration in minutes (default 25)
            tags: Optional tags

        Returns:
            Success/error message
        """
        # Check if already tracking
        active = self.storage.load_active_session()
        if active:
            return f"❌ Already tracking: {active['task']}\nStop current session first."

        # Validate task name
        validation_error = self._validate_task_name(task)
        if validation_error:
            return validation_error

        task = task.strip()
        tags = tags or []

        start_time = datetime.now().isoformat()
        self.storage.save_active_session(task, start_time, tags)

        # Add pomodoro-specific data
        active = self.storage.load_active_session()
        active['pomodoro'] = True
        active['pomodoro_duration'] = duration

        # Save updated session
        with open(self.storage.active_file, 'w') as f:
            import json
            json.dump(active, f, indent=2)

        return f"🍅 Pomodoro started: {task} ({duration} min)"

    def pomodoro_status(self) -> str:
        """Show pomodoro status with remaining time."""
        active = self.storage.load_active_session()

        if not active:
            return "No active pomodoro"

        if not active.get('pomodoro'):
            return "Current session is not a pomodoro"

        try:
            start_time = datetime.fromisoformat(active['start_time'])
        except (ValueError, KeyError):
            return "❌ Error: Invalid session data"

        duration = active.get('pomodoro_duration', 25)
        elapsed = datetime.now() - start_time
        elapsed_minutes = int(elapsed.total_seconds() / 60)
        remaining = max(0, duration - elapsed_minutes)

        remaining_min = remaining
        remaining_sec = max(0, int((duration * 60) - elapsed.total_seconds()) % 60)

        count = self.get_pomodoro_count()

        return f"🍅 Pomodoro: {active['task']}\n⏱ Remaining: {remaining_min:02d}:{remaining_sec:02d}\n📊 Today's pomodoros: {count}"

    def pomodoro_stop(self) -> str:
        """Cancel current pomodoro without saving."""
        active = self.storage.load_active_session()

        if not active:
            return "❌ No active pomodoro to cancel"

        task = active.get('task', 'Unknown')
        self.storage.clear_active_session()

        return f"🍅 Pomodoro cancelled: {task}"

    def pomodoro_complete(self) -> str:
        """Complete pomodoro and save session."""
        active = self.storage.load_active_session()

        if not active:
            return "❌ No active pomodoro"

        try:
            start_time = datetime.fromisoformat(active['start_time'])
        except (ValueError, KeyError):
            return "❌ Error: Invalid session data"

        end_time = datetime.now()
        duration = end_time - start_time

        tags = active.get('tags', [])
        if 'pomodoro' not in tags:
            tags.append('pomodoro')

        self.storage.save_completed_session(
            task=active['task'],
            start_time=active['start_time'],
            end_time=end_time.isoformat(),
            duration_seconds=int(duration.total_seconds()),
            tags=tags
        )

        self.storage.clear_active_session()

        hours, remainder = divmod(int(duration.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)

        count = self.get_pomodoro_count()

        return f"🍅 Pomodoro complete: {active['task']}\n⏱ Duration: {hours}h {minutes}m\n📊 Today's pomodoros: {count}"

    def get_pomodoro_count(self) -> int:
        """Get count of completed pomodoros today."""
        today = datetime.now().date().isoformat()
        history = self.storage.load_history()

        count = 0
        for session in history:
            try:
                if session['start_time'].startswith(today):
                    tags = session.get('tags', [])
                    if 'pomodoro' in tags:
                        count += 1
            except (KeyError, TypeError):
                continue

        return count

    def start_break(self, long_break: bool = None) -> str:
        """
        Start a break timer.

        Args:
            long_break: Force long break (15 min) if True, short break (5 min) if False.
                        If None, auto-detect based on pomodoro count.

        Returns:
            Break message
        """
        count = self.get_pomodoro_count()

        # Auto-detect break type
        if long_break is None:
            long_break = (count % 4 == 0 and count > 0)

        if long_break:
            duration = 15
            break_type = "Long break"
        else:
            duration = 5
            break_type = "Short break"

        return f"☕ {break_type}: {duration} minutes\n🍅 Pomodoros completed today: {count}"


def interactive_mode():
    """Run interactive menu for time tracking."""
    tracker = TimeTracker()

    while True:
        # Show current status
        click.echo("\n" + "=" * 40)
        click.echo("TIME TRACKER")
        click.echo("=" * 40)

        active = tracker.storage.load_active_session()
        if active:
            start_time = datetime.fromisoformat(active['start_time'])
            elapsed = datetime.now() - start_time
            hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            click.echo(f"Currently tracking: {active['task']}")
            click.echo(f"Elapsed: {hours}h {minutes}m {seconds}s")
        else:
            click.echo("Not tracking any task")

        click.echo("\n[1] Start new task")
        click.echo("[2] Stop current task")
        click.echo("[3] Show status")
        click.echo("[4] Daily report")
        click.echo("[5] Weekly report")
        click.echo("[6] Monthly report")
        click.echo("[7] Export to CSV")
        click.echo("[0] Exit")

        choice = click.prompt("\nSelect option", type=str, default="0")

        if choice == "1":
            task = click.prompt("Task name")
            click.echo(tracker.start(task))
        elif choice == "2":
            click.echo(tracker.stop())
        elif choice == "3":
            click.echo(tracker.status())
        elif choice == "4":
            date = click.prompt("Date (YYYY-MM-DD, or press Enter for today)", default="", show_default=False)
            click.echo(tracker.report(date if date else None))
        elif choice == "5":
            week = click.prompt("Week start date (YYYY-MM-DD, or press Enter for current)", default="", show_default=False)
            click.echo(tracker.report_weekly(week if week else None))
        elif choice == "6":
            month = click.prompt("Month (YYYY-MM, or press Enter for current)", default="", show_default=False)
            click.echo(tracker.report_monthly(month if month else None))
        elif choice == "7":
            output = click.prompt("Output file", default="time_tracker_export.csv")
            start_date = click.prompt("Start date filter (YYYY-MM-DD, or press Enter to skip)", default="", show_default=False)
            end_date = click.prompt("End date filter (YYYY-MM-DD, or press Enter to skip)", default="", show_default=False)
            click.echo(tracker.export_csv(
                output,
                start_date if start_date else None,
                end_date if end_date else None
            ))
        elif choice == "0":
            click.echo("Goodbye!")
            break
        else:
            click.echo("Invalid option, try again")

        click.pause()


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Simple time tracking CLI tool.

    Run without arguments for interactive mode.
    """
    if ctx.invoked_subcommand is None:
        interactive_mode()


@cli.command()
@click.argument('task')
@click.option('--tag', '-t', multiple=True, help='Add tag to session (can use multiple times)')
def start(task, tag):
    """Start tracking a task."""
    tracker = TimeTracker()
    click.echo(tracker.start(task, tags=list(tag) if tag else None))


@cli.command()
def stop():
    """Stop the current task."""
    tracker = TimeTracker()
    click.echo(tracker.stop())


@cli.command()
def status():
    """Show current tracking status."""
    tracker = TimeTracker()
    click.echo(tracker.status())


@cli.command()
@click.option('--date', default=None, help='Date in YYYY-MM-DD format')
@click.option('--week', 'report_type', flag_value='week', help='Show weekly report')
@click.option('--month', 'report_type', flag_value='month', help='Show monthly report')
@click.option('--tag', '-t', default=None, help='Filter by tag')
@click.argument('period', required=False)
def report(date, report_type, period, tag):
    """Show report for date/week/month (defaults to today)."""
    tracker = TimeTracker()

    if report_type == 'week':
        click.echo(tracker.report_weekly(period))
    elif report_type == 'month':
        click.echo(tracker.report_monthly(period))
    else:
        click.echo(tracker.report(date, tag=tag))


@cli.command()
@click.option('--output', '-o', default=None, help='Output CSV file path')
@click.option('--start-date', default=None, help='Start date (YYYY-MM-DD)')
@click.option('--end-date', default=None, help='End date (YYYY-MM-DD)')
@click.option('--tag', '-t', default=None, help='Filter by tag')
def export(output, start_date, end_date, tag):
    """Export sessions to CSV file."""
    tracker = TimeTracker()
    click.echo(tracker.export_csv(output, start_date, end_date, tag=tag))


@cli.command()
@click.option('--simple', is_flag=True, help='Use simple mode (no live updates)')
def tui(simple):
    """Launch beautiful TUI dashboard with live timer."""
    from .tui import run_tui, run_tui_simple

    if simple:
        run_tui_simple()
    else:
        try:
            run_tui()
        except Exception:
            # Fallback to simple mode on error
            run_tui_simple()


@cli.command()
@click.option('--setup', is_flag=True, help='Configure bot token and settings')
@click.option('--token', default=None, help='Bot token (overrides config)')
def bot(setup, token):
    """Run Telegram bot with reminders."""
    from .telegram_bot import run_bot, setup_bot

    if setup:
        setup_bot()
    else:
        run_bot(token)


@cli.group()
def pomodoro():
    """Pomodoro timer commands."""
    pass


@pomodoro.command('start')
@click.argument('task')
@click.option('--duration', '-d', default=25, help='Duration in minutes (default 25)')
@click.option('--tag', '-t', multiple=True, help='Add tag to session')
def pomodoro_start_cmd(task, duration, tag):
    """Start a pomodoro session."""
    tracker = TimeTracker()
    click.echo(tracker.pomodoro_start(task, duration, tags=list(tag) if tag else None))


@pomodoro.command('status')
def pomodoro_status_cmd():
    """Show pomodoro status and remaining time."""
    tracker = TimeTracker()
    click.echo(tracker.pomodoro_status())


@pomodoro.command('stop')
def pomodoro_stop_cmd():
    """Cancel current pomodoro."""
    tracker = TimeTracker()
    click.echo(tracker.pomodoro_stop())


@pomodoro.command('complete')
def pomodoro_complete_cmd():
    """Mark pomodoro as complete and save."""
    tracker = TimeTracker()
    click.echo(tracker.pomodoro_complete())


@pomodoro.command('break')
@click.option('--long', 'long_break', is_flag=True, help='Start long break (15 min)')
def pomodoro_break_cmd(long_break):
    """Start a break (5 min short, 15 min long)."""
    tracker = TimeTracker()
    click.echo(tracker.start_break(long_break if long_break else None))


if __name__ == '__main__':
    cli()
