from django.core.management.base import BaseCommand
from qa.models import Project, TestCase


class Command(BaseCommand):
    help = "Create the sample Task Manager project and its test cases"

    def handle(self, *args, **options):
        project, _ = Project.objects.get_or_create(
            name="Task Management System",
            defaults={
                "base_url": "http://127.0.0.1:8001",
                "description": (
                    "Django Task Management System. "
                    "BugPilot uses it as the real system under test."
                ),
            },
        )
        project.base_url = "http://127.0.0.1:8001"
        project.save()

        cases = [
            {
                "title": "Login page is available",
                "test_type": "http",
                "preconditions": "Task Manager server is running on port 8001.",
                "steps": "Send GET request to /accounts/login/.",
                "expected_result": "HTTP 200 and the Login page is returned.",
                "path": "/accounts/login/",
                "expected_status": 200,
                "expected_text": "Login",
            },
            {
                "title": "Registration page is available",
                "test_type": "http",
                "preconditions": "Task Manager server is running on port 8001.",
                "steps": "Send GET request to /register/.",
                "expected_result": "HTTP 200 and Create Account is returned.",
                "path": "/register/",
                "expected_status": 200,
                "expected_text": "Create Account",
            },
            {
                "title": "Unauthenticated user is redirected to login",
                "test_type": "manual",
                "preconditions": "User has no active session.",
                "steps": "1. Open the root URL / in an incognito window.\n2. Observe navigation.",
                "expected_result": "User is redirected to the Django login page.",
            },
            {
                "title": "Valid user can log in",
                "test_type": "manual",
                "preconditions": "QA seed command has been executed.",
                "steps": (
                    "1. Open /accounts/login/.\n"
                    "2. Enter qa_user / QApass123!.\n"
                    "3. Click Login."
                ),
                "expected_result": "Dashboard is shown and qa_user appears in the header.",
            },
            {
                "title": "User can create a task",
                "test_type": "manual",
                "preconditions": "qa_user is logged in.",
                "steps": (
                    "1. Open Create Task.\n"
                    "2. Fill title, description, priority and due date.\n"
                    "3. Save."
                ),
                "expected_result": "New task appears on the dashboard with entered values.",
            },
            {
                "title": "User can edit and complete a task",
                "test_type": "manual",
                "preconditions": "At least one qa_user task exists.",
                "steps": "1. Click Edit.\n2. Change title.\n3. Mark Completed.\n4. Save.",
                "expected_result": "Updated title is visible and status is Completed.",
            },
            {
                "title": "Search returns matching tasks",
                "test_type": "manual",
                "preconditions": "QA Baseline High Priority task exists.",
                "steps": "1. Enter Baseline in Search tasks.\n2. Click Apply.",
                "expected_result": "Matching task is shown and unrelated tasks are hidden.",
            },
            {
                "title": "Priority filter returns only selected priority",
                "test_type": "manual",
                "preconditions": "High and Low priority QA tasks exist.",
                "steps": "1. Choose High priority.\n2. Click Apply.",
                "expected_result": "Only High priority tasks belonging to the user are shown.",
            },
            {
                "title": "Normal user cannot see another user's tasks",
                "test_type": "manual",
                "preconditions": "qa_other owns PRIVATE OTHER USER TASK; qa_user is logged in.",
                "steps": "1. Open dashboard.\n2. Search for PRIVATE OTHER USER TASK.",
                "expected_result": "The other user's task is not visible to qa_user.",
            },
            {
                "title": "User can delete own task",
                "test_type": "manual",
                "preconditions": "qa_user owns a disposable task.",
                "steps": "1. Click Delete.\n2. Confirm Yes, Delete.",
                "expected_result": "Task disappears from the user's dashboard.",
            },
        ]

        for case in cases:
            case_data = case.copy()
            title = case_data.pop("title")
            TestCase.objects.update_or_create(
                project=project,
                title=title,
                defaults=case_data,
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Sample project and test cases are ready for http://127.0.0.1:8001."
            )
        )
