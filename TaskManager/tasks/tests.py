from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .forms import RegisterForm
from .models import Task

User = get_user_model()


class TaskModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="modeluser", password="SafePass123!")

    def test_task_string_representation(self):
        task = Task.objects.create(title="Prepare report", owner=self.user)
        self.assertEqual(str(task), "Prepare report")

    def test_task_defaults(self):
        task = Task.objects.create(title="Default task", owner=self.user)
        self.assertFalse(task.is_completed)
        self.assertEqual(task.priority, "medium")
        self.assertEqual(task.description, "")
        self.assertIsNone(task.due_date)


class RegistrationTests(TestCase):
    def test_registration_creates_and_logs_in_user(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "email": "new@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertRedirects(response, reverse("task_list"))
        self.assertTrue(User.objects.filter(username="newuser").exists())
        self.assertIn("_auth_user_id", self.client.session)

    def test_duplicate_email_is_rejected_case_insensitively(self):
        User.objects.create_user(
            username="existing",
            email="user@example.com",
            password="StrongPass123!",
        )
        form = RegisterForm(
            data={
                "username": "another",
                "email": "USER@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_authenticated_user_is_redirected_from_register_page(self):
        user = User.objects.create_user(username="alreadyin", password="StrongPass123!")
        self.client.force_login(user)
        response = self.client.get(reverse("register"))
        self.assertRedirects(response, reverse("task_list"))


class TaskViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="SafePass123!")
        self.other_user = User.objects.create_user(username="bob", password="SafePass123!")
        self.staff = User.objects.create_user(
            username="staff",
            password="SafePass123!",
            is_staff=True,
        )

        self.own_task = Task.objects.create(
            title="Alice private task",
            description="Visible only to Alice",
            owner=self.user,
            priority="high",
            is_completed=False,
        )
        self.other_task = Task.objects.create(
            title="Bob private task",
            description="Visible only to Bob",
            owner=self.other_user,
            priority="low",
            is_completed=True,
        )

    def test_dashboard_requires_authentication(self):
        response = self.client.get(reverse("task_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_normal_user_sees_only_own_tasks(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("task_list"))

        self.assertContains(response, self.own_task.title)
        self.assertNotContains(response, self.other_task.title)
        self.assertEqual(response.context["total_tasks"], 1)

    def test_staff_user_still_sees_only_tasks_they_own(self):
        staff_task = Task.objects.create(
            title="Staff user's own task",
            owner=self.staff,
            priority="medium",
        )
        self.client.force_login(self.staff)
        response = self.client.get(reverse("task_list"))

        self.assertContains(response, staff_task.title, html=True)
        self.assertNotContains(response, self.own_task.title)
        self.assertNotContains(response, self.other_task.title)
        self.assertEqual(response.context["total_tasks"], 1)

    def test_create_task_assigns_current_user_as_owner(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("task_create"),
            {
                "title": "Created through form",
                "description": "",
                "priority": "medium",
                "due_date": "",
            },
        )

        self.assertRedirects(response, reverse("task_list"))
        task = Task.objects.get(title="Created through form")
        self.assertEqual(task.owner, self.user)
        self.assertFalse(task.is_completed)

    def test_user_cannot_open_another_users_task_for_update(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("task_update", args=[self.other_task.pk]))
        self.assertEqual(response.status_code, 404)

    def test_user_cannot_delete_another_users_task(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("task_delete", args=[self.other_task.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Task.objects.filter(pk=self.other_task.pk).exists())

    def test_staff_user_cannot_update_or_delete_another_users_task(self):
        self.client.force_login(self.staff)

        update_response = self.client.get(
            reverse("task_update", args=[self.other_task.pk])
        )
        delete_response = self.client.post(
            reverse("task_delete", args=[self.other_task.pk])
        )

        self.assertEqual(update_response.status_code, 404)
        self.assertEqual(delete_response.status_code, 404)
        self.assertTrue(Task.objects.filter(pk=self.other_task.pk).exists())

    def test_user_can_update_own_task(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("task_update", args=[self.own_task.pk]),
            {
                "title": "Updated title",
                "description": "Updated description",
                "priority": "medium",
                "due_date": "",
                "is_completed": "on",
            },
        )

        self.assertRedirects(response, reverse("task_list"))
        self.own_task.refresh_from_db()
        self.assertEqual(self.own_task.title, "Updated title")
        self.assertTrue(self.own_task.is_completed)

    def test_user_can_delete_own_task(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("task_delete", args=[self.own_task.pk]))

        self.assertRedirects(response, reverse("task_list"))
        self.assertFalse(Task.objects.filter(pk=self.own_task.pk).exists())

    def test_search_matches_title_and_description(self):
        Task.objects.create(
            title="Unrelated title",
            description="Contains the keyword satellite",
            owner=self.user,
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse("task_list"), {"search": "satellite"})

        tasks = list(response.context["tasks"])
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].description, "Contains the keyword satellite")

    def test_guest_cannot_access_task_mutation_pages(self):
        for url in (
            reverse("task_create"),
            reverse("task_update", args=[self.own_task.pk]),
            reverse("task_delete", args=[self.own_task.pk]),
        ):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("login"), response.url)

    def test_search_does_not_return_another_users_task(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("task_list"), {"search": "Bob private"}
        )
        self.assertEqual(list(response.context["tasks"]), [])

    def test_delete_confirmation_does_not_delete_before_post(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("task_delete", args=[self.own_task.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Task.objects.filter(pk=self.own_task.pk).exists())

    def test_task_description_is_rendered_as_text_not_executable_html(self):
        unsafe_description = '<script>alert("xss")</script>'
        self.own_task.description = unsafe_description
        self.own_task.save(update_fields=["description"])
        self.client.force_login(self.user)

        response = self.client.get(reverse("task_list"))

        self.assertNotContains(response, unsafe_description)
        self.assertContains(
            response,
            "&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;",
        )

    def test_dashboard_counters_are_not_changed_by_filters(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("task_list"), {"status": "completed", "priority": "low"}
        )
        self.assertEqual(list(response.context["tasks"]), [])
        self.assertEqual(response.context["total_tasks"], 1)
        self.assertEqual(response.context["in_progress_tasks"], 1)
        self.assertEqual(response.context["completed_tasks"], 0)

    def test_status_and_priority_filters_can_be_combined(self):
        matching = Task.objects.create(
            title="Completed high priority",
            owner=self.user,
            priority="high",
            is_completed=True,
        )
        Task.objects.create(
            title="Completed low priority",
            owner=self.user,
            priority="low",
            is_completed=True,
        )
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("task_list"),
            {"status": "completed", "priority": "high"},
        )

        self.assertEqual(list(response.context["tasks"]), [matching])


class SeedQaCommandTests(TestCase):
    def test_seed_command_is_repeatable_and_preserves_unrelated_tasks(self):
        unrelated_user = User.objects.create_user(
            username="regular_dev",
            password="SafePass123!",
        )
        unrelated_task = Task.objects.create(
            owner=unrelated_user,
            title="Keep this task",
            description="The seed command must not delete unrelated user data.",
        )

        call_command("seed_qa", stdout=StringIO())
        call_command("seed_qa", stdout=StringIO())

        qa_user = User.objects.get(username="qa_user")
        other_user = User.objects.get(username="qa_other")
        self.assertTrue(qa_user.check_password("QApass123!"))
        self.assertTrue(other_user.check_password("OtherPass123!"))
        self.assertFalse(qa_user.is_staff)
        self.assertEqual(Task.objects.filter(owner=qa_user).count(), 2)
        self.assertEqual(Task.objects.filter(owner=other_user).count(), 1)
        self.assertTrue(Task.objects.filter(pk=unrelated_task.pk).exists())
