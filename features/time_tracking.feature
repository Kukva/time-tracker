Feature: Track work time
  As a freelance developer
  I want to track my work sessions
  So that I can invoice clients accurately

  Scenario: Start new work session
    Given I am not currently tracking time
    When I run "track start 'coding homework'"
    Then I should see "✓ Session started: coding homework"
    And current session should be active
    And session should have start timestamp

  Scenario: Stop active session and save
    Given I have an active session "fixing bugs"
    When I run "track stop"
    Then I should see session duration
    And session should be saved to history file
    And current session should be cleared

  Scenario: Cannot start when already tracking
    Given I have an active session "writing docs"
    When I run "track start 'new task'"
    Then I should see error "Already tracking: writing docs"
    And previous session should remain active

  Scenario: View current status
    Given I have an active session "code review"
    When I run "track status"
    Then I should see current task name
    And I should see elapsed time

  Scenario: Show daily report
    Given I have completed 3 sessions today
    When I run "track report today"
    Then I should see list of all sessions
    And I should see total time worked

  Scenario: Export sessions to CSV
    Given I have completed sessions in history
    When I run "track export"
    Then a CSV file should be created
    And CSV file should contain session data
    And I should see success message with file path

  Scenario: Export sessions with date filter
    Given I have sessions from multiple dates
    When I run "track export --start-date 2026-01-01 --end-date 2026-01-31"
    Then CSV should only contain sessions in date range
    And I should see count of exported sessions

  Scenario: Export to custom file path
    Given I have completed sessions
    When I run "track export -o my_report.csv"
    Then file should be created at "my_report.csv"
    And file should have .csv extension

  Scenario: Export with no sessions
    Given I have no completed sessions
    When I run "track export"
    Then I should see error "No sessions to export"
    And no CSV file should be created

  Scenario: View weekly report
    Given I have sessions from current week
    When I run "track report --week"
    Then I should see all sessions from Monday to Sunday
    And I should see total hours for the week
    And sessions should be grouped by day

  Scenario: View specific week report
    Given I have sessions from multiple weeks
    When I run "track report --week 2026-01-06"
    Then I should see sessions for week starting 2026-01-06
    And I should see 7 days in the report

  Scenario: Weekly report with no sessions
    Given I have no sessions this week
    When I run "track report --week"
    Then I should see "No sessions recorded for this week"

  Scenario: View monthly report
    Given I have sessions from current month
    When I run "track report --month"
    Then I should see all sessions from the month
    And I should see total hours for the month
    And sessions should be grouped by day

  Scenario: View specific month report
    Given I have sessions from multiple months
    When I run "track report --month 2026-01"
    Then I should see sessions for January 2026
    And I should see month name in header

  Scenario: Monthly report with no sessions
    Given I have no sessions this month
    When I run "track report --month"
    Then I should see "No sessions recorded for this month"

  # ============ RICH TUI SCENARIOS ============

  Scenario: Launch TUI dashboard
    Given I have the rich library installed
    When I run "track tui"
    Then I should see a formatted dashboard
    And I should see the status panel
    And I should see the actions panel

  Scenario: TUI shows live timer when tracking
    Given I have an active session "coding"
    When I view the TUI dashboard
    Then I should see the task name "coding"
    And I should see elapsed time updating
    And the timer should be highlighted in green

  Scenario: TUI shows idle state when not tracking
    Given I am not currently tracking time
    When I view the TUI dashboard
    Then I should see "Not tracking" status
    And the status should be highlighted in yellow

  Scenario: Start task from TUI
    Given I am viewing the TUI dashboard
    And I am not currently tracking time
    When I press "1" to start a task
    And I enter task name "new feature"
    Then tracking should start for "new feature"
    And the dashboard should update to show active status

  Scenario: Stop task from TUI
    Given I am viewing the TUI dashboard
    And I have an active session "bug fixing"
    When I press "2" to stop tracking
    Then tracking should stop
    And I should see session summary
    And the dashboard should update to show idle status

  Scenario: View today's sessions in TUI
    Given I have completed 3 sessions today
    When I view the TUI dashboard
    Then I should see today's sessions panel
    And I should see total time worked today

  Scenario: Exit TUI gracefully
    Given I am viewing the TUI dashboard
    When I press "q" to quit
    Then the TUI should close cleanly
    And I should return to normal terminal

  # ============ TELEGRAM BOT SCENARIOS ============

  Scenario: Start tracking via Telegram
    Given the Telegram bot is configured
    And I am not currently tracking time
    When I send "/start coding feature" to the bot
    Then I should receive "Session started: coding feature"
    And tracking should be active

  Scenario: Stop tracking via Telegram
    Given the Telegram bot is configured
    And I have an active session "bug fixing"
    When I send "/stop" to the bot
    Then I should receive session summary
    And tracking should be stopped

  Scenario: Check status via Telegram
    Given the Telegram bot is configured
    And I have an active session "writing docs"
    When I send "/status" to the bot
    Then I should receive current task info
    And I should see elapsed time

  Scenario: Get daily report via Telegram
    Given the Telegram bot is configured
    And I have completed sessions today
    When I send "/report" to the bot
    Then I should receive today's session list
    And I should see total hours

  Scenario: Receive reminder for long session
    Given the Telegram bot is configured
    And I have been tracking "long task" for 4 hours
    When the reminder check runs
    Then I should receive a reminder message
    And the message should ask if I forgot to stop

  Scenario: Receive daily summary
    Given the Telegram bot is configured
    And daily summary is enabled for 18:00
    And I have completed sessions today
    When it is 18:00
    Then I should receive daily summary notification
    And it should show total hours worked

  Scenario: Bot help command
    Given the Telegram bot is configured
    When I send "/help" to the bot
    Then I should receive list of available commands