# BugPilot

BugPilot is a small Django app for keeping QA work for web projects in one place. It is developed alongside the included TaskManager sample, which is used for the example test cases.

## What it does

- Stores project details and the target application's URL.
- Keeps manual test cases and simple HTTP GET checks.
- Saves manual and HTTP results in run history.
- Tracks bugs, including reproduction steps, severity and status.
- Imports source ZIP files without running their contents.
- Provides a dashboard and project-specific views.

The Playwright suite in `automation/` tests both web interfaces through a browser. It also launches the two sample HTTP test cases through BugPilot's UI against the running TaskManager app. Playwright results are still separate from BugPilot's own run history.

## Start BugPilot

Install the packages from the repository root, then run these commands from this directory:

```bash
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 127.0.0.1:8000
```

Open `http://127.0.0.1:8000/`. The dashboard links to projects, test cases, run history, bug reports and the usage guide.

The environment badge in the header reads `BUGPILOT_ENVIRONMENT` from `BugPilot/.env`. Leave it empty to use `Development` when `DJANGO_DEBUG=True` or `Production` when `DJANGO_DEBUG=False`; set it to `CI`, `Staging` or another label when needed. It reflects configuration, not an automatic check of where the server is hosted. Restart the server after changing `.env`.

## Add a project

For a running application, open **Projects → Add project** and enter its URL. For a source archive, choose **Projects → Import ZIP**. ZIP import only stores the files; it does not install dependencies or execute code. Start the imported app separately and add its URL to the project record before creating HTTP checks.

HTTP checks send a GET request to the project URL plus the configured path. They compare the response status code and, if specified, a piece of expected text. Manual cases can be marked PASS, FAIL or ERROR with notes.

## Tests

Django tests for BugPilot:

```bash
python manage.py test
```

Browser tests require TaskManager to be running at `http://127.0.0.1:8001/` and BugPilot at `http://127.0.0.1:8000/`. The URLs can be overridden with `TASK_MANAGER_BASE_URL` and `BUGPILOT_BASE_URL`; `QA_USERNAME` and `QA_PASSWORD` configure the disposable TaskManager test account:

```bash
python -m pytest automation -v
```

See the repository root `README.md` for setup instructions and the QA documents in `qa_docs/` for the test plan and cases.

## Local data

Project records, cases, runs and bugs are stored in `db.sqlite3`. Imported files are stored in `uploaded_projects/`. These are local runtime data, not source files. On a fresh checkout, migrations create the database and `seed_demo` creates or updates the sample cases. The command does not remove unrelated projects or cases.
