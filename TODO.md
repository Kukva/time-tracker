# Project Roadmap

## Completed Features

### Core Functionality
- [x] Basic commands: start, stop, status, report (#3, #4, #5)
- [x] Task name validation (#9, #11)
- [x] Corrupted JSON handling (#11)
- [x] CSV export with date filtering (#8)
- [x] Weekly reports (#2)
- [x] Monthly reports (#2)
- [x] **Tags/Categories** for sessions
  - Multiple tags per session: `--tag work --tag python`
  - Filter reports by tag: `--tag client`
  - Filter exports by tag
  - Tags displayed in status and reports
- [x] **Pomodoro Timer** mode
  - 25 min work sessions (customizable)
  - 5 min short breaks / 15 min long breaks
  - Auto long break after 4 pomodoros
  - Pomodoro count tracking per day
  - Commands: start, status, complete, stop, break

### User Interface
- [x] Interactive CLI mode
- [x] **Rich TUI Dashboard** with live timer (#13, #14, #15)
  - Live updating timer display
  - Color-coded status panels
  - Today's sessions summary
  - Keyboard navigation
- [x] **Telegram Bot** with reminders (#17, #18, #19)
  - Commands: /start, /stop, /status, /report, /week, /month, /help
  - Automatic reminders for long sessions (>4 hours)
  - Daily summary notifications
  - Config stored in ~/.timetracker/telegram.json

### Testing & Quality
- [x] Unit tests (70+ tests)
- [x] BDD tests with pytest-bdd (39 scenarios)
- [x] TUI component tests (16 tests)
- [x] Telegram bot tests (18 tests)
- [x] Tags tests (8 tests)
- [x] Pomodoro tests (10 tests)
- [x] Test coverage >80%

## In Progress

*No items currently in progress*

## Backlog

### High Priority
- [ ] CI/CD with GitHub Actions

### Nice to Have
- [ ] Desktop notifications
- [ ] Data visualization / charts
- [ ] Config file support (.timetracker.yml)

### Technical Debt
- [ ] SQLite migration (#12)
- [ ] Logging framework (#11, #12)
- [ ] File permission checks (#11)
- [ ] Timezone handling (#12)
- [ ] Better code comments

## Issue References

| Issue | Title | Status |
|-------|-------|--------|
| #1 | Need time tracking tool | Open (meta) |
| #2 | MVP Feature Set | Closed |
| #3-5 | Core commands | Closed |
| #6 | Test suite | Closed |
| #7 | AI code review | Closed |
| #8 | CSV export | Closed |
| #9 | Task validation | Closed |
| #10 | Telegram integration | Closed |
| #11 | Security improvements | Open (partial) |
| #12 | Medium/Low priority | Closed |
| #13-15 | Rich TUI | Closed |
| #17-19 | Telegram bot + reminders | Closed |
