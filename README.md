# Time Tracker CLI

Simple CLI time tracking tool for freelancers.

## Project Status

**Test Coverage: 85% (37 tests)**

See [GitHub Issues](../../issues) for full project history and roadmap.

### Completed Features
- [x] Basic commands: start, stop, status, report (#3, #4, #5)
- [x] Test suite with >80% coverage (#6)
- [x] Task name validation (#9, #11)
- [x] Corrupted JSON handling (#11)
- [x] CSV export with date filtering (#8)
- [x] Weekly reports (#2)
- [x] Monthly reports (#2)

### Open Issues (Backlog)
- [ ] Telegram bot integration (#10)
- [ ] SQLite migration (#12)
- [ ] Logging framework (#11, #12)
- [ ] File permission checks (#11)
- [ ] Timezone handling (#12)

## Problem
Losing billable hours due to forgetting to track time.

## Solution
Minimal CLI: `track start/stop/status/report/export`

## Installation
```bash
pip install -r requirements.txt
pip install -e .
```

## Usage

### Basic Commands
```bash
track start "coding homework"   # Start tracking a task
track status                    # Show current task and elapsed time
track stop                      # Stop tracking and save session
track report                    # Show today's sessions
```

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

## Development
```bash
pytest tests/ -v --cov=src
```