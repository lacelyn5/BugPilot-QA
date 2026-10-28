# TaskManager QA Checklist

Run this checklist against the local TaskManager app. Mark an item only after checking it and record a bug report for any unexpected result.

## Authentication and access

- [ ] A new user can register with a valid username, email and password.
- [ ] A duplicate email address is rejected, regardless of letter case.
- [ ] A user can log in with valid credentials and log out.
- [ ] Opening `/` without a session redirects to the login page.
- [ ] A guest cannot create, edit or delete tasks.
- [ ] User A cannot see User B's task on the dashboard or in search results.
- [ ] User A receives a 404 when trying to edit or delete User B's task.
- [ ] Django's staff flag does not bypass task ownership in the dashboard or direct edit/delete URLs.

## Task workflows

- [ ] A task can be created with a title, description, priority and due date.
- [ ] Description and due date can be left empty.
- [ ] Title, description, priority, due date and completion status persist after editing.
- [ ] A task cannot be deleted before the confirmation is submitted.
- [ ] Search matches both title and description.
- [ ] Completed and In progress filters return the expected tasks.
- [ ] High, Medium and Low priority filters return the expected tasks.
- [ ] Status and priority filters work together.
- [ ] Dashboard counters remain based on all of the current user's tasks, even when filters are active.
- [ ] Resetting filters restores the full task list.

## Layout

- [ ] A long uninterrupted title stays inside the task card.
- [ ] A long uninterrupted description wraps instead of overflowing.
- [ ] The layout remains usable at a narrow mobile viewport (around 375 px).
- [ ] A long description does not break the edit form.

## Automated checks

Check the migrations and run Django tests for both applications, then run Playwright:

```bash
cd TaskManager
python manage.py makemigrations --check --dry-run
python manage.py test
cd ../BugPilot
python manage.py makemigrations --check --dry-run
python manage.py test
python -m pytest automation -v
```

The browser suite requires TaskManager on port 8001 and BugPilot on port 8000. GitHub Actions runs the Django test suites and browser checks on each push and pull request.
