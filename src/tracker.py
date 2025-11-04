import click
from datetime import datetime, timedelta
from typing import Optional
from .storage import Storage

class TimeTracker:
    """Main time tracking logic."""
    
    def __init__(self):
        self.storage = Storage()
    
    def start(self, task: str) -> str:
        """Start tracking a new task."""
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
        
        start_time = datetime.fromisoformat(active['start_time'])
        end_time = datetime.now()
        duration = end_time - start_time
        
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
        
        start_time = datetime.fromisoformat(active['start_time'])
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
        
        filtered_sessions = [
            s for s in history 
            if s['start_time'].startswith(target_date)
        ]
        
        if not filtered_sessions:
            return f"No sessions on {target_date}"
        
        total_seconds = sum(s['duration_seconds'] for s in filtered_sessions)
        total_hours, remainder = divmod(total_seconds, 3600)
        total_minutes, _ = divmod(remainder, 60)
        
        output = [f"📊 Report for {target_date}", "=" * 40]
        
        for session in filtered_sessions:
            start = datetime.fromisoformat(session['start_time'])
            hours, remainder = divmod(session['duration_seconds'], 3600)
            minutes, _ = divmod(remainder, 60)
            
            output.append(
                f"{start.strftime('%H:%M')} | {session['task']} | {hours}h {minutes}m"
            )
        
        output.append("=" * 40)
        output.append(f"Total: {total_hours}h {total_minutes}m")
        
        return "\n".join(output)


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


if __name__ == '__main__':
    cli()