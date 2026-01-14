# Time Tracker CLI

Simple CLI time tracking tool for freelancers. Built with TDD/BDD methodology.

## Project Status

**Test Coverage: 85% (52 tests: 37 unit + 15 BDD)**

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

### Open Issues (Backlog)
- [ ] Telegram bot integration (#10)
- [ ] SQLite migration (#12)
- [ ] Logging framework (#11, #12)
- [ ] File permission checks (#11)
- [ ] Timezone handling (#12)

## Problem
Losing billable hours due to forgetting to track time.

## Solution
Minimal CLI with interactive mode: `track` for menu or `track <command>` for direct use

## Installation
```bash
pip install -r requirements.txt
pip install -e .
```

## Usage

### Interactive Mode
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