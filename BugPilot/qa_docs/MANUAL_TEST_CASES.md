# Manual Test Cases — Task Management System

These titles match the cases created by `python manage.py seed_demo` in BugPilot. The TC numbers in this document are stable documentation references; the numeric IDs displayed in the UI are database primary keys and may have gaps after records are deleted. Each procedure below can be performed manually. The browser suite also exercises the two HTTP smoke checks and the main task workflows.

## TC-001 — Login page is available
**Priority:** High  
**Preconditions:** TaskManager is running and the BugPilot sample project points to its base URL.

**Steps**
1. Open **Test cases** in BugPilot.
2. Open **Login page is available**.
3. Click **Run check now**.

**Expected result**  
The saved result is PASS, the endpoint responds with HTTP 200, and the response contains the login page text.

## TC-002 — Registration page is available
**Priority:** High  
**Preconditions:** TaskManager is running and the BugPilot sample project points to its base URL.

**Steps**
1. Open **Test cases** in BugPilot.
2. Open **Registration page is available**.
3. Click **Run check now**.

**Expected result**  
The saved result is PASS, the endpoint responds with HTTP 200, and the response contains the registration page text.

## TC-003 — Unauthenticated user is redirected to login
**Priority:** High  
**Preconditions:** No user is logged in.

**Steps**
1. Open the TaskManager root URL `/` in a private browser window.

**Expected result**
The browser is redirected to `/accounts/login/?next=/` and the login form is displayed.

## TC-004 — Valid user can log in
**Priority:** High  
**Preconditions:** Run `python manage.py seed_qa` in TaskManager.

**Steps**
1. Open `/accounts/login/`.
2. Enter `qa_user` and `QApass123!`.
3. Click **Login**.

**Expected result**
The dashboard opens and the signed-in username is shown.

## TC-005 — User can create a task
**Priority:** High  
**Preconditions:** `qa_user` is signed in.

**Steps**
1. Click **+ Create Task**.
2. Enter a title and description.
3. Choose a priority and a future due date.
4. Click **Save Task**.

**Expected result**
The new task appears with the values entered in the form and an In progress status.

## TC-006 — User can edit and complete a task
**Priority:** High  
**Preconditions:** `qa_user` owns at least one task.

**Steps**
1. Click **Edit** on the task.
2. Change its title.
3. Select **Completed** and save.

**Expected result**
The new title is displayed and the task status is Completed.

## TC-007 — Search returns matching tasks
**Priority:** Medium  
**Preconditions:** The seeded task `QA Baseline High Priority` exists.

**Steps**
1. Enter `Baseline` in the search field.
2. Click **Apply**.

**Expected result**
The matching task is displayed and unrelated tasks are not shown.

## TC-008 — Priority filter returns only selected priority
**Priority:** Medium  
**Preconditions:** `qa_user` has tasks with different priorities.

**Steps**
1. Select **High priority**.
2. Click **Apply**.

**Expected result**
Every displayed task has High priority.

## TC-009 — Normal user cannot see another user's tasks
**Priority:** Critical  
**Preconditions:** `qa_other` owns `PRIVATE OTHER USER TASK`; `qa_user` is signed in.

**Steps**
1. Open the dashboard as `qa_user`.
2. Search for `PRIVATE OTHER USER TASK`.

**Expected result**
The other user's task is not displayed.

## TC-010 — User can delete own task
**Priority:** High  
**Preconditions:** `qa_user` owns a disposable task.

**Steps**
1. Click **Delete** on the task.
2. Confirm **Yes, Delete**.

**Expected result**
The task is removed from the dashboard.
