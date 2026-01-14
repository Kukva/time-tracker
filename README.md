# Time Tracker CLI

Simple CLI time tracking tool for freelancers. Built with TDD/BDD methodology.

## Project Status

**Test Coverage: 85% (100+ tests: unit + BDD + TUI + Telegram)**

See [GitHub Issues](../../issues) for full project history and roadmap.

### Completed Features
- [x] Basic commands: start, stop, status, report (#3, #4, #5)
- [x] Test suite with >80% coverage (#6)
- [x] Task name validation (#9, #11)
- [x] Corrupted JSON handling (#11)
- [x] CSV export with date filtering (#8)
- [x] Weekly reports (#2)
- [x] Monthly reports (#2)
- [x] BDD tests with pytest-bdd (step definitions)
- [x] Interactive CLI mode
- [x] **Rich TUI Dashboard** with live timer (#13, #14, #15)
- [x] **Telegram Bot** with reminders (#17, #18, #19)
- [x] **Tags/Categories** for sessions
- [x] **Pomodoro Timer** with breaks

### Open Issues (Backlog)
- [ ] SQLite migration (#12)
- [ ] Logging framework (#11, #12)
- [ ] File permission checks (#11)
- [ ] Timezone handling (#12)

## Problem
Losing billable hours due to forgetting to track time.

## Solution
Feature-rich CLI with multiple interfaces:
- **TUI Dashboard** - Beautiful terminal UI with live timer (`track tui`)
- **Interactive Menu** - Guided menu interface (`track`)
- **Direct Commands** - Quick CLI commands (`track start/stop/...`)
- **Telegram Bot** - Control from anywhere with reminders (`track bot`)

## Installation
```bash
pip install -r requirements.txt
pip install -e .
```

## Usage

### TUI Dashboard (Recommended)
```bash
track tui                       # Launch beautiful TUI dashboard
track tui --simple              # Simple mode (cross-platform)
```
The TUI dashboard provides:
- **Live timer** updating every second
- Color-coded status (green=tracking, yellow=idle)
- Today's sessions panel with totals
- Keyboard shortcuts for all actions

### Interactive Menu
```bash
track                           # Launch interactive menu
```
The interactive menu provides:
- Current tracking status display
- All commands accessible via numbered menu
- Guided prompts for dates and options

### Basic Commands
```bash
track start "coding homework"   # Start tracking a task
track status                    # Show current task and elapsed time
track stop                      # Stop tracking and save session
track report                    # Show today's sessions
```

### Tags
```bash
track start "coding" --tag work --tag python   # Start with multiple tags
track start "meeting" -t client -t billable    # Short form -t
track report --tag work                        # Filter report by tag
track export --tag client -o client_hours.csv  # Export only tagged sessions
```
Tags help organize sessions by project, client, or category.

### Pomodoro Timer
```bash
track pomodoro start "deep work"       # Start 25 min pomodoro
track pomodoro start "task" -d 15      # Custom duration (15 min)
track pomodoro status                  # Show remaining time
track pomodoro complete                # Complete and save session
track pomodoro stop                    # Cancel without saving
track pomodoro break                   # Start break (5 min)
track pomodoro break --long            # Long break (15 min)
```

**Pomodoro Technique:**
- 🍅 Work for 25 minutes (1 pomodoro)
- ☕ Short break: 5 minutes
- 🌴 Long break: 15 minutes (after 4 pomodoros)
- Completed pomodoros are auto-tagged with `pomodoro`

### Reports
```bash
track report                    # Daily report (today)
track report --date 2026-01-15  # Report for specific date
track report --week             # Weekly report (current week)
track report --week 2026-01-06  # Weekly report for specific week
track report --month            # Monthly report (current month)
track report --month 2026-01    # Monthly report for specific month
```

### Export
```bash
track export                              # Export all sessions to CSV
track export -o my_report.csv             # Export to custom file
track export --start-date 2026-01-01      # Filter by start date
track export --end-date 2026-01-31        # Filter by end date
```

### Telegram Bot
```bash
track bot --setup                         # Configure bot token
track bot                                 # Run Telegram bot
```

**Bot Commands:**
- `/start <task>` - Start tracking a task
- `/stop` - Stop tracking
- `/status` - Show current status
- `/report` - Today's report
- `/week` - Weekly report
- `/month` - Monthly report
- `/help` - Show available commands

**Features:**
- Automatic reminders for sessions > 4 hours
- Daily summary notifications
- Control tracking from anywhere via Telegram

**Setup:**
1. Create bot via [@BotFather](https://t.me/BotFather)
2. Run `track bot --setup` and enter your token
3. Run `track bot` to start the bot

## Development

### Running Tests
```bash
# All tests (unit + BDD)
pytest tests/ -v --cov=src

# Only BDD tests
pytest tests/test_bdd.py -v

# Only unit tests
pytest tests/test_tracker.py tests/test_storage.py -v
```

### TDD/BDD Workflow
This project follows Test-Driven Development:
1. Write BDD scenarios in `features/*.feature`
2. Write step definitions in `tests/test_bdd.py`
3. Write unit tests in `tests/test_*.py`
4. Implement functionality
5. Verify all tests pass

See `CLAUDE.md` for AI-assisted development guidelines.