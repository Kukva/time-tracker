import click
import csv
from datetime import datetime, timedelta
from typing import Optional
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
    
    def start(self, task: str) -> str:
        """Start tracking a new task."""
        # Validate task name
        validation_error = self._validate_task_name(task)
        if validation_error:
            return validation_error
        
        # Trim whitespace
        task = task.strip()
        
        active = self.storage.load_active_session()
        
        if active:
            return f"❌ Already tracking: {active['task']}\nStop current session first."
        
        start_time = datetime.now().isoformat()
        self.storage.save_active_session(task, start_time)
        return f"✓ Session started: {task}"
    
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
        
        self.storage.save_completed_session(
            task=active['task'],
            start_time=active['start_time'],
            end_time=end_time.isoformat(),
            duration_seconds=int(duration.total_seconds())
        )
        
        self.storage.clear_active_session()
        
        hours, remainder = divmod(int(duration.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)
        
        return f"✓ Session stopped: {active['task']}\nDuration: {hours}h {minutes}m"
    
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
        
        return f"📍 Tracking: {active['task']}\nElapsed: {hours}h {minutes}m"
    
    def report(self, date: Optional[str] = None) -> str:
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
                    filtered_sessions.append(session)
            except (KeyError, TypeError):
                # Skip malformed sessions
                continue
        
        if not filtered_sessions:
            return f"No sessions on {target_date}"
        
        total_seconds = sum(s.get('duration_seconds', 0) for s in filtered_sessions)
        total_hours, remainder = divmod(total_seconds, 3600)
        total_minutes, _ = divmod(remainder, 60)
        
        output = [f"📊 Report for {target_date}", "=" * 40]
        
        for session in filtered_sessions:
            try:
                start = datetime.fromisoformat(session['start_time'])
                hours, remainder = divmod(session['duration_seconds'], 3600)
                minutes, _ = divmod(remainder, 60)
                
                output.append(
                    f"{start.strftime('%H:%M')} | {session['task']} | {hours}h {minutes}m"
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
                   end_date: Optional[str] = None) -> str:
        """
        Export sessions to CSV file.

        Args:
            output_file: Path to output CSV file (defaults to ./time_tracker_export.csv)
            start_date: Filter sessions from this date (YYYY-MM-DD format)
            end_date: Filter sessions until this date (YYYY-MM-DD format)

        Returns:
            Success/error message
        """
        history = self.storage.load_history()

        if not history:
            return "❌ No sessions to export"

        # Filter by date range if specified
        filtered_sessions = []
        for session in history:
            try:
                session_date = session['start_time'][:10]  # Extract YYYY-MM-DD

                # Check date range
                if start_date and session_date < start_date:
                    continue
                if end_date and session_date > end_date:
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
                    'task', 'start_time', 'end_time', 'duration_hours', 'duration_minutes'
                ])
                writer.writeheader()

                for session in filtered_sessions:
                    try:
                        hours, remainder = divmod(session['duration_seconds'], 3600)
                        minutes, _ = divmod(remainder, 60)

                        writer.writerow({
                            'task': session['task'],
                            'start_time': session['start_time'],
                            'end_time': session['end_time'],
                            'duration_hours': hours,
                            'duration_minutes': minutes
                        })
                    except (KeyError, TypeError):
                        # Skip malformed entries
                        continue

            return f"✓ Exported {len(filtered_sessions)} sessions to {output_path.absolute()}"

        except (IOError, PermissionError) as e:
            return f"❌ Error writing CSV file: {e}"


@click.group()
def cli():
    """Simple time tracking CLI tool."""
    pass


@cli.command()
@click.argument('task')
def start(task):
    """Start tracking a task."""
    tracker = TimeTracker()
    click.echo(tracker.start(task))


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
def report(date):
    """Show report for date (defaults to today)."""
    tracker = TimeTracker()
    click.echo(tracker.report(date))


@cli.command()
@click.option('--output', '-o', default=None, help='Output CSV file path')
@click.option('--start-date', default=None, help='Start date (YYYY-MM-DD)')
@click.option('--end-date', default=None, help='End date (YYYY-MM-DD)')
def export(output, start_date, end_date):
    """Export sessions to CSV file."""
    tracker = TimeTracker()
    click.echo(tracker.export_csv(output, start_date, end_date))


if __name__ == '__main__':
    cli()
