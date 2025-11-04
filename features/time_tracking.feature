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