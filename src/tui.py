"""Rich TUI for Time Tracker with live timer."""
import sys
import time
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich.align import Align
from rich import box

from .tracker import TimeTracker


console = Console()


def format_elapsed_time(seconds: int) -> str:
    """Format seconds into HH:MM:SS string."""
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def get_status_style(tracker: TimeTracker) -> str:
    """Get color style based on tracking status."""
    active = tracker.storage.load_active_session()
    return "green" if active else "yellow"


def build_status_panel(tracker: TimeTracker) -> Panel:
    """Build the status panel showing current tracking state."""
    active = tracker.storage.load_active_session()

    if active:
        task = active['task']
        start_time = datetime.fromisoformat(active['start_time'])
        elapsed = datetime.now() - start_time
        elapsed_str = format_elapsed_time(int(elapsed.total_seconds()))

        content = Table.grid(padding=1)
        content.add_column(justify="right", style="bold")
        content.add_column(justify="left")

        content.add_row("Task:", Text(task, style="cyan bold"))
        content.add_row("Elapsed:", Text(elapsed_str, style="green bold on black"))
        content.add_row("Started:", start_time.strftime("%H:%M:%S"))

        return Panel(
            Align.center(content),
            title="[green bold]TRACKING[/green bold]",
            border_style="green",
            box=box.DOUBLE
        )
    else:
        content = Text("Not tracking any task", style="yellow italic")
        return Panel(
            Align.center(content),
            title="[yellow]IDLE[/yellow]",
            border_style="yellow",
            box=box.ROUNDED
        )


def build_actions_panel() -> Panel:
    """Build the actions panel with available commands."""
    table = Table.grid(padding=(0, 2))
    table.add_column(justify="center", style="bold cyan")
    table.add_column(justify="left")

    table.add_row("[1]", "Start new task")
    table.add_row("[2]", "Stop tracking")
    table.add_row("[3]", "Show status")
    table.add_row("[4]", "Daily report")
    table.add_row("[5]", "Weekly report")
    table.add_row("[6]", "Monthly report")
    table.add_row("[7]", "Export CSV")
    table.add_row("[q]", "Quit")

    return Panel(
        table,
        title="[bold]Actions[/bold]",
        border_style="blue",
        box=box.ROUNDED
    )


def build_sessions_panel(tracker: TimeTracker) -> Panel:
    """Build panel showing today's completed sessions."""
    today = datetime.now().date().isoformat()
    history = tracker.storage.load_history()

    # Filter today's sessions
    today_sessions = [
        s for s in history
        if s.get('start_time', '').startswith(today)
    ]

    if not today_sessions:
        content = Text("No sessions today", style="dim italic")
        total_text = "0h 0m"
    else:
        table = Table(box=box.SIMPLE, padding=(0, 1))
        table.add_column("Task", style="cyan")
        table.add_column("Duration", justify="right", style="green")

        total_seconds = 0
        for session in today_sessions[-5:]:  # Last 5 sessions
            task = session.get('task', 'Unknown')[:20]
            duration = session.get('duration_seconds', 0)
            total_seconds += duration

            hours, remainder = divmod(duration, 3600)
            minutes, _ = divmod(remainder, 60)
            duration_str = f"{hours}h {minutes}m"

            table.add_row(task, duration_str)

        content = table

        total_hours, total_remainder = divmod(total_seconds, 3600)
        total_minutes, _ = divmod(total_remainder, 60)
        total_text = f"{total_hours}h {total_minutes}m"

    return Panel(
        content,
        title=f"[bold]Today's Sessions[/bold] [dim]({total_text})[/dim]",
        border_style="magenta",
        box=box.ROUNDED
    )


def build_header() -> Panel:
    """Build the header panel."""
    title = Text()
    title.append("TIME TRACKER", style="bold white on blue")
    title.append(" ", style="default")
    title.append("TUI", style="bold cyan")

    return Panel(
        Align.center(title),
        box=box.DOUBLE,
        style="blue"
    )


def create_layout(tracker: TimeTracker) -> Layout:
    """Create the full TUI layout."""
    layout = Layout()

    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3)
    )

    layout["body"].split_row(
        Layout(name="left"),
        Layout(name="right", size=30)
    )

    layout["left"].split_column(
        Layout(name="status", size=8),
        Layout(name="sessions")
    )

    # Fill layout
    layout["header"].update(build_header())
    layout["status"].update(build_status_panel(tracker))
    layout["sessions"].update(build_sessions_panel(tracker))
    layout["right"].update(build_actions_panel())
    layout["footer"].update(
        Panel(
            "[dim]Press number to select action, 'q' to quit[/dim]",
            box=box.ROUNDED
        )
    )

    return layout


def get_task_input() -> str:
    """Get task name input from user."""
    console.print("\n[cyan]Enter task name:[/cyan] ", end="")
    return input().strip()


def handle_input(key: str, tracker: TimeTracker) -> str:
    """Handle user input and return action result."""
    if key.lower() == "q":
        return "quit"

    if key == "1":
        task = get_task_input()
        if task:
            result = tracker.start(task)
            console.print(f"\n[green]{result}[/green]")
        return "continue"

    elif key == "2":
        result = tracker.stop()
        console.print(f"\n[yellow]{result}[/yellow]")
        return "continue"

    elif key == "3":
        result = tracker.status()
        console.print(f"\n{result}")
        time.sleep(2)
        return "continue"

    elif key == "4":
        result = tracker.report()
        console.print(f"\n{result}")
        console.input("\n[dim]Press Enter to continue...[/dim]")
        return "continue"

    elif key == "5":
        result = tracker.report_weekly()
        console.print(f"\n{result}")
        console.input("\n[dim]Press Enter to continue...[/dim]")
        return "continue"

    elif key == "6":
        result = tracker.report_monthly()
        console.print(f"\n{result}")
        console.input("\n[dim]Press Enter to continue...[/dim]")
        return "continue"

    elif key == "7":
        console.print("\n[cyan]Output file (Enter for default):[/cyan] ", end="")
        output = input().strip() or "time_tracker_export.csv"
        result = tracker.export_csv(output)
        console.print(f"\n[green]{result}[/green]")
        time.sleep(2)
        return "continue"

    return "continue"


def run_tui():
    """Run the TUI with live updates."""
    tracker = TimeTracker()

    console.clear()
    console.print("[bold blue]Starting Time Tracker TUI...[/bold blue]\n")

    try:
        with Live(create_layout(tracker), refresh_per_second=1, screen=True) as live:
            while True:
                # Update layout
                live.update(create_layout(tracker))

                # Check for input (non-blocking would be better, but keeping simple)
                # For now, we'll use a simple approach
                import msvcrt
                if msvcrt.kbhit():
                    key = msvcrt.getch().decode('utf-8', errors='ignore')

                    if key.lower() == 'q':
                        break

                    # Handle input
                    live.stop()
                    result = handle_input(key, tracker)
                    if result == "quit":
                        break
                    live.start()

                time.sleep(0.1)

    except KeyboardInterrupt:
        pass

    console.clear()
    console.print("[bold green]Goodbye![/bold green]")


def run_tui_simple():
    """Run simplified TUI without live updates (cross-platform)."""
    tracker = TimeTracker()

    while True:
        console.clear()
        console.print(create_layout(tracker))
        console.print()

        key = console.input("[bold cyan]Select option:[/bold cyan] ")

        result = handle_input(key, tracker)
        if result == "quit":
            break

    console.print("[bold green]Goodbye![/bold green]")
