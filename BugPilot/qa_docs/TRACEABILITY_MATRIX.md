# Test Traceability — Task Management System

This matrix maps the ten seeded BugPilot test cases to checks in the repository. The IDs displayed in the BugPilot UI are based on database primary keys and may have gaps after records are deleted; use the test title as the stable reference when reviewing results.

| Test case | Requirement / behavior | Automated coverage |
|---|---|---|
| TC-001 — Login page is available | The login endpoint returns the expected page | BugPilot browser smoke test `test_http_smoke_case_returns_pass[Login page is available]`; service behavior is covered by `HttpRunnerTests` |
| TC-002 — Registration page is available | The registration endpoint returns the expected page | BugPilot browser smoke test `test_http_smoke_case_returns_pass[Registration page is available]`; service behavior is covered by `HttpRunnerTests` |
| TC-003 — Unauthenticated user is redirected to login | Guests cannot open the task dashboard | `test_unauthenticated_dashboard_redirects_to_login`; `TaskViewTests.test_dashboard_requires_authentication` |
| TC-004 — Valid user can log in | A valid QA account can open the dashboard | `test_valid_login_shows_only_the_users_own_tasks`; the Django registration test separately verifies the registration flow |
| TC-005 — User can create a task | A new task is saved with the submitted fields | `test_user_can_create_a_task`; `TaskViewTests.test_create_task_assigns_current_user_as_owner` |
| TC-006 — User can edit and complete a task | Task fields and completion state can be updated | `test_user_can_edit_and_complete_a_task`; `TaskViewTests.test_user_can_update_own_task` |
| TC-007 — Search returns matching tasks | Search matches task titles and descriptions | `test_search_returns_matching_tasks`; `TaskViewTests.test_search_matches_title_and_description` |
| TC-008 — Priority filter returns only selected priority | Results respect the selected priority | `test_priority_filter_shows_only_the_selected_priority`; `TaskViewTests.test_status_and_priority_filters_can_be_combined` |
| TC-009 — Normal user cannot see another user's tasks | Task visibility is limited to its owner | `test_user_cannot_find_another_users_task`; `TaskViewTests.test_search_does_not_return_another_users_task`; `TaskViewTests.test_user_cannot_open_another_users_task_for_update` |
| TC-010 — User can delete own task | A user can delete their own task after confirmation | `test_user_can_delete_own_task`; `TaskViewTests.test_delete_confirmation_does_not_delete_before_post`; `TaskViewTests.test_user_can_delete_own_task` |

## BugPilot workflow coverage

The BugPilot browser suite also checks project creation/deletion, running the built-in HTTP tests against the live TaskManager app, recording and deleting a manual run, editing and deleting a bug report, and the ZIP-import guidance. Django tests separately cover ZIP validation, destructive-action confirmation and HTTP-runner error paths.

The built-in HTTP runner and the Playwright suite are separate systems. Playwright results remain in the test-run output and are not automatically written into BugPilot's run history.
