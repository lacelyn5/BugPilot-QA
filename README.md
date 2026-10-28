# BugPilot + Task Management System

This repository contains two small Django applications used together for QA practice:

- **TaskManager** is the application under test. It supports accounts, personal tasks, priorities, due dates, search and filters.
- **BugPilot** is a lightweight workspace for project records, manual and HTTP test cases, execution history and bug reports.

The repository includes Django tests for both applications, Playwright end-to-end checks for both UIs, a Postman collection and QA notes. The browser suite also runs BugPilot's built-in HTTP checks against the live TaskManager instance.

The BugPilot mark combines a bug, an orbit and a check: identify an issue, keep it in view, then verify the result. The interface uses one guide entry and an environment badge driven by configuration rather than claiming the app is always private or running on the same machine.

## Run locally on Windows

You need Python 3.12 or newer. From the repository root, run:

```bat
setup_windows.bat
```

The script creates a virtual environment, installs the requirements, installs Chromium for Playwright, applies migrations and loads disposable test data. It resets tasks owned by the dedicated QA users, so use it with a local development database only.

Then start both applications:

```bat
run_apps_windows.bat
```

| Application | Address |
|---|---|
| TaskManager | http://127.0.0.1:8001/ |
| BugPilot | http://127.0.0.1:8000/ |

For local browser testing, the fixture account is `qa_user` with password `QApass123!`. It is only for the disposable development data created by `seed_qa`.

## Run the tests

Activate the root virtual environment first:

```bat
.venv\Scripts\activate
```

Django tests for TaskManager:

```bat
cd TaskManager
python manage.py test
```

Django tests for BugPilot:

```bat
cd ..\BugPilot
python manage.py test
```

Playwright browser tests (both applications must be running):

```bat
python -m pytest automation -v
```

The same checks run in `.github/workflows/qa.yml` on pushes and pull requests. CI checks Python syntax, both Django configurations and migrations, runs both Django test suites, starts both servers, and then runs Playwright. Failed browser tests save screenshots under `BugPilot/artifacts/screenshots/`; GitHub Actions uploads available screenshots and server logs as the `qa-failure-diagnostics` artifact.

## What the checks cover

- Login and registration pages respond as expected.
- Unauthenticated visitors are redirected to login.
- Users can create, edit, complete, search, filter and delete their own tasks.
- A regular user cannot access another user's tasks.
- BugPilot can save manual results, run simple HTTP GET checks and track defects.
- ZIP imports reject unsafe paths and never execute the uploaded source code.

BugPilot's HTTP runner performs bounded GET checks for an expected status and optional response text. It reports redirects as the response from the configured endpoint rather than following them to another host. Playwright exercises both applications and verifies this HTTP-runner integration; Playwright results themselves are not automatically added to BugPilot's run history.

## Add another project

Start the application separately, then use **Projects → Add project** in BugPilot and enter its base URL. You can also import a ZIP to store its source files; import does not install dependencies or start the application. Once the app is running, edit the project record and add its URL.

For details, see the in-app **How to use** page and `BugPilot/README.md`.

## QA notes

- `BugPilot/qa_docs/TEST_PLAN.md` — scope and test approach
- `BugPilot/qa_docs/MANUAL_TEST_CASES.md` — manual cases corresponding to the seeded case IDs
- `BugPilot/qa_docs/TRACEABILITY_MATRIX.md` — links between cases and automated checks
- `BugPilot/qa_docs/CHECKLIST.md` — quick regression checklist
- `BugPilot/qa_docs/BUG_REPORT_TEMPLATE.md` — bug report structure
- `BugPilot/qa_docs/SQL_EXAMPLES.sql` — basic queries against the TaskManager schema

SQLite databases and imported project files are local runtime data and are not included in the repository. On a fresh checkout, the setup script creates the databases and sample records. The seed commands reset only the dedicated QA users' tasks in TaskManager and create or update the sample BugPilot cases; they do not remove unrelated project records.

Both applications use development settings. Do not expose the local servers or sample credentials to the public internet.

### Environment label

The label in BugPilot's header is configurable; it is not a detector for the physical machine or hosting provider. Set `BUGPILOT_ENVIRONMENT` in `BugPilot/.env` to `Development`, `CI`, `Staging` or `Production` when you need a specific label. If it is empty, BugPilot displays `Development` when `DJANGO_DEBUG=True` and `Production` when `DJANGO_DEBUG=False`. Update the value in each environment so the label describes the configuration you are running.
