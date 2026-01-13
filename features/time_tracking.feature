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