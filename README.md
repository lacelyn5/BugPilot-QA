
# BugPilot — QA Management Platform

**A Django-based QA workspace built alongside a Task Management application for practical software testing and automation.**

[![QA Checks](https://github.com/lacelyn5/BugPilot-QA/actions/workflows/qa.yml/badge.svg)](https://github.com/lacelyn5/BugPilot-QA/actions/workflows/qa.yml)
![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-6.0-092E20?logo=django&logoColor=white)
![pytest](https://img.shields.io/badge/pytest-testing-0A9EDC?logo=pytest&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-browser%20testing-2EAD33?logo=playwright&logoColor=white)
![Postman](https://img.shields.io/badge/Postman-API%20testing-FF6C37?logo=postman&logoColor=white)

## Overview

BugPilot is a lightweight QA management platform developed with Django. It is designed to organize testing activities for web projects, including test cases, execution results, and defect tracking.

The repository also contains a separate **TaskManager** application used as the application under test (AUT). Together, the two applications provide an environment for practising manual testing, HTTP checks, Django testing, and browser automation.

The project combines web development with practical QA workflows in one integrated environment.

## Applications

### BugPilot — QA Management Platform

BugPilot provides a workspace for organizing and tracking testing activities.

Main features:

- Project management and target application URLs.
- Manual test case creation and management.
- Simple HTTP GET checks with expected status and response text.
- Test execution history for manual and HTTP results.
- Bug reports with severity, status, and reproduction steps.
- Project-specific views and dashboard.
- ZIP source import with path validation and archive limits.
- In-app usage guide.

### TaskManager — Application Under Test

TaskManager is a separate Django web application used to test BugPilot workflows.

Main features:

- User registration and authentication.
- Personal task management.
- Task priorities and due dates.
- Search and filtering.
- Task creation, editing, completion, and deletion.
- User-level task ownership protection.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.12+ | Main programming language |
| Django 6 | Web applications |
| SQLite | Local development databases |
| pytest | Test execution |
| pytest-django | Django testing support |
| Playwright | Browser automation |
| Requests | HTTP testing |
| Postman | API request collection |
| GitHub Actions | Continuous integration |

## Quick Start — Windows

### Requirements

- Windows 10 or 11.
- Python 3.12 or newer.
- Python Launcher (`py`).
- Internet connection for installing dependencies and downloading Chromium.

### 1. Set up the project

Clone or download the repository and open its root folder in Command Prompt.

Run the setup script:

```bat
setup_windows.bat
```

The script automatically:

1. Checks the Python version.
2. Creates the `.venv` virtual environment.
3. Installs the required Python packages.
4. Installs Chromium for Playwright.
5. Applies TaskManager database migrations.
6. Creates disposable TaskManager QA data.
7. Applies BugPilot database migrations.
8. Creates or updates sample BugPilot test cases.

**Important:** The setup script resets tasks belonging to dedicated QA users. Use it with a local development database, not with production data.

### 2. Start both applications

After setup completes, run:

```bat
run_apps_windows.bat
```

The script opens both applications in separate terminal windows.

| Application | Local address |
|---|---|
| TaskManager | http://127.0.0.1:8001/ |
| BugPilot | http://127.0.0.1:8000/ |

Open the BugPilot dashboard in your browser:

**http://127.0.0.1:8000/**

### 3. Local test account

The setup script creates disposable QA data.

For local browser testing, the default TaskManager fixture account is:

- Username: `qa_user`
- Password: `QApass123!`

These credentials are only for the disposable local development database created by the `seed_qa` command. Do not reuse them for real accounts or expose the development servers to the public internet.

## Running Tests

Activate the virtual environment from the repository root:

```bat
.venv\Scripts\activate
```

### TaskManager Django tests

```bat
cd TaskManager
python manage.py test
```

### BugPilot Django tests

Return to the repository root, then enter the BugPilot folder:

```bat
cd ..
cd BugPilot
python manage.py test
```

### Playwright browser tests

Both applications must be running:

- TaskManager: `http://127.0.0.1:8001/`
- BugPilot: `http://127.0.0.1:8000/`

From the `BugPilot` folder, run:

```bat
python -m pytest automation -v
```

The browser suite checks both application interfaces and verifies BugPilot's HTTP-runner integration with the running TaskManager application.

## What the Tests Cover

### TaskManager

- Registration and login.
- Authentication and protected pages.
- Creating, editing, completing, and deleting tasks.
- Search and priority/status filters.
- User ownership and access restrictions.
- Safe rendering of user-provided descriptions.

### BugPilot

- Project, test case, and bug report management.
- Manual test execution and result history.
- HTTP status and response text checks.
- Timeouts and invalid targets.
- Confirmation of destructive actions.
- ZIP archive path validation and import safety.

### Browser Automation

Playwright tests cover real browser workflows in both applications.

They also launch BugPilot's built-in HTTP checks against the running TaskManager application.

**Note:** Playwright results are not automatically added to BugPilot's own execution history.

## Continuous Integration

The project includes a GitHub Actions workflow:

`.github/workflows/qa.yml`

CI runs automatically on pushes and pull requests.

The workflow performs:

- Python syntax validation.
- Django configuration checks.
- Migration consistency checks.
- TaskManager Django tests.
- BugPilot Django tests.
- Local startup checks for both applications.
- Playwright browser regression tests.

It uses Python 3.13 and installs Chromium for browser automation.

When a workflow fails, available browser screenshots and diagnostic server logs are uploaded as a GitHub Actions artifact named `qa-failure-diagnostics`.

## Working With Another Project

BugPilot can be used to organize QA activities for other running web applications.

To add another project:

1. Start the target application separately.
2. Open BugPilot.
3. Navigate to **Projects → Add project**.
4. Enter the application's base URL.
5. Configure manual test cases or HTTP checks.

BugPilot also supports importing a ZIP archive through **Projects → Import ZIP**.

**ZIP import limitations:**

- Imported files are stored inside BugPilot.
- Dependencies are not installed automatically.
- Imported applications are not started automatically.
- Uploaded source code is not executed.

Start the imported application separately and add its URL to the project record before configuring HTTP checks.

## QA Documentation

The repository includes structured testing documentation:

| Document | Description |
|---|---|
| `TEST_PLAN.md` | Testing scope, objectives, and approach |
| `MANUAL_TEST_CASES.md` | Manual test cases |
| `TRACEABILITY_MATRIX.md` | Links between test cases and automated checks |
| `CHECKLIST.md` | Quick regression checklist |
| `BUG_REPORT_TEMPLATE.md` | Defect reporting template |
| `SQL_EXAMPLES.sql` | Basic SQL examples for the TaskManager database |

All QA documents are located in:

`BugPilot/qa_docs/`

## Project Structure

```text
BugPilot-QA/
│
├── .github/
│   └── workflows/
│       └── qa.yml
│
├── BugPilot/
│   ├── automation/
│   ├── qa_docs/
│   ├── manage.py
│   └── README.md
│
├── TaskManager/
│   ├── manage.py
│   └── ...
│
├── requirements.txt
├── setup_windows.bat
├── run_apps_windows.bat
├── run_bugpilot_windows.bat
├── run_taskmanager_windows.bat
└── README.md
```

## Known Limitations

This project is designed as a local development and QA practice environment.

- Both applications use development settings and SQLite databases.
- The HTTP runner currently supports GET checks rather than arbitrary HTTP methods or request bodies.
- HTTP checks compare the configured response status and optional expected text.
- Redirects are reported from the configured endpoint rather than followed to another host.
- Playwright results remain separate from BugPilot's own run history.
- ZIP imports store source files but do not install dependencies or execute uploaded code.
- Load testing, full penetration testing, email delivery, external identity providers, and a general-purpose REST API are outside the current scope.

Do not expose the local development servers or sample credentials to the public internet.

## Environment Label

The environment label displayed in BugPilot's header is configurable through `BUGPILOT_ENVIRONMENT` in `BugPilot/.env`.

Supported examples include:

- `Development`
- `CI`
- `Staging`
- `Production`

When the variable is empty, the application displays `Development` when `DJANGO_DEBUG=True` and `Production` when `DJANGO_DEBUG=False`.

The label reflects the configured environment. It does not automatically detect where the application is hosted.

Restart the server after changing the environment configuration.

## Project Purpose

BugPilot was developed as a practical project combining Django web development and software QA workflows.

It demonstrates:

- Building and maintaining web applications with Django.
- Organizing manual testing activities.
- Implementing basic HTTP checks.
- Writing automated Django tests.
- Creating browser-based Playwright tests.
- Using Postman and structured QA documentation.
- Integrating automated checks into GitHub Actions.

---

**Created by Maksim Kernazhytski**
