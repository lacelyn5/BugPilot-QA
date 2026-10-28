# Test Plan — Task Management System and BugPilot

## Objective

Verify the TaskManager workflows used as the system under test and the BugPilot workflows used to record, execute and review QA activity.

## Scope

**TaskManager**
- registration and login;
- authentication requirements for protected pages;
- create, edit, complete and delete tasks;
- search and combined status/priority filters;
- ownership isolation for regular and staff users;
- safe rendering of user-supplied descriptions.

**BugPilot**
- creating and editing projects, test cases and bug reports;
- recording manual results and reviewing run history;
- HTTP status/text checks, timeouts and invalid targets;
- confirmation of destructive actions;
- ZIP path validation, extraction limits and non-execution of imported source code.

## Out of scope

Load testing, full penetration testing, email delivery, external identity providers and a general-purpose REST API are not implemented in this version. The HTTP runner currently supports GET checks rather than arbitrary HTTP methods or request bodies. Playwright results are not automatically imported into BugPilot's own run history.

## Test environment

- Python 3.12 or 3.13;
- Django and SQLite;
- TaskManager at `http://127.0.0.1:8001`;
- BugPilot at `http://127.0.0.1:8000`;
- Chromium for Playwright tests;
- disposable accounts and tasks created by `python manage.py seed_qa`;
- the Task Management System project and ten sample test cases created by `python manage.py seed_demo`.

## Test approach

- Django tests cover view behavior, form validation, data ownership, ZIP validation and HTTP-runner outcomes without depending on external websites.
- Playwright tests cover real browser workflows in both applications, including the integration from BugPilot's HTTP runner to the running TaskManager app.
- The manual test cases and checklist support hands-on exploratory checks. They complement automation rather than claiming every manual step is a separate automated test.

## Entry criteria

- Dependencies are installed.
- Both applications have been migrated and the QA seed commands have completed.
- The two local servers are reachable at the configured addresses.
- The Playwright Chromium browser is installed.

## Exit criteria

- Both Django test suites pass.
- All Playwright tests pass against the two running applications.
- Migration checks report no model changes without migrations.
- Any remaining failure has a reproducible report and a documented disposition.
