# Task Management System

A Django web application for organizing personal tasks and tracking progress.

## Features

- Registration, login, logout and protected pages
- Task creation, editing, completion and deletion
- Priority levels and optional due dates
- Search by title or description and filter by priority or completion
- Dashboard statistics
- Per-user task isolation; staff privileges do not expose other users' tasks in the dashboard
- Responsive templates and CSS
- Automated Django test suite

## Technology

Python, Django, SQLite, Django ORM, HTML/CSS and Django templates.

## Start locally

From the `TaskManager/` directory:

```bash
python manage.py migrate
python manage.py runserver 127.0.0.1:8001
```

Open `http://127.0.0.1:8001/`.

The shared workspace setup installs dependencies from the root `requirements.txt`.

## Tests

```bash
python manage.py test
```

For integration tests with BugPilot, prepare isolated local test users and task records:

```bash
python manage.py seed_qa
```

**`seed_qa` resets tasks belonging to its dedicated test users.** Run it only in a disposable local development database.

## Project layout

- `config/` — Django project settings and routing
- `tasks/` — models, forms, views, routes, templates and tests
- `static/` — interface styling
- `../BugPilot/qa_docs/CHECKLIST.md` — manual verification checklist

Local SQLite databases, `.env` and cache files are not committed.
