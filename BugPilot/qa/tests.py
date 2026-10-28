import io
from io import StringIO
import shutil
import stat
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

import requests

from django.conf import settings
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase as DjangoTestCase
from django.test import override_settings
from django.urls import reverse

from .models import BugReport, Project, TestCase, TestRun
from .services import run_http_test


class WorkspaceViewTests(DjangoTestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Smoke project",
            base_url="http://127.0.0.1:8002",
            description="Project used by workspace tests",
        )
        self.manual_case = TestCase.objects.create(
            project=self.project,
            title="Profile page displays correctly",
            test_type="manual",
            steps="Open the profile page",
            expected_result="The profile page is displayed",
        )

    def test_dashboard_and_project_pages_render(self):
        urls = [
            reverse("dashboard"),
            reverse("project_list"),
            reverse("project_detail", args=[self.project.pk]),
            reverse("create_project"),
            reverse("edit_project", args=[self.project.pk]),
            reverse("upload_project_zip"),
        ]
        for url in urls:
            with self.subTest(page=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_test_case_and_run_pages_render(self):
        run = TestRun.objects.create(
            test_case=self.manual_case,
            status="PASS",
            actual_result="The profile page opened successfully.",
        )
        urls = [
            reverse("test_list"),
            reverse("create_test_case"),
            reverse("edit_test_case", args=[self.manual_case.pk]),
            reverse("test_detail", args=[self.manual_case.pk]),
            reverse("run_list"),
            reverse("delete_run", args=[run.pk]),
        ]
        for url in urls:
            with self.subTest(page=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_bug_pages_render(self):
        bug = BugReport.objects.create(
            project=self.project,
            title="Profile page shows an error",
            steps_to_reproduce="Open the profile page",
            expected_result="The profile page is displayed",
            actual_result="An error message is displayed",
        )
        urls = [
            reverse("bug_list"),
            reverse("create_bug"),
            reverse("edit_bug", args=[bug.pk]),
            reverse("bug_detail", args=[bug.pk]),
            reverse("guide"),
        ]
        for url in urls:
            with self.subTest(page=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    @override_settings(BUGPILOT_ENVIRONMENT="Staging")
    def test_shared_layout_has_one_guide_entry_and_configured_environment(self):
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Staging")
        self.assertContains(response, "How to use")
        self.assertContains(response, "brand-mark.svg")
        self.assertNotContains(response, "Open quick guide")
        self.assertNotContains(response, "Private · on this machine")
        self.assertNotContains(response, "Local environment")

    def test_project_can_be_created_from_ui(self):
        response = self.client.post(
            reverse("create_project"),
            {
                "name": "Second project",
                "base_url": "http://127.0.0.1:8003",
                "description": "Another running web app",
            },
        )

        project = Project.objects.get(name="Second project")
        self.assertRedirects(response, reverse("project_detail", args=[project.pk]))
        self.assertEqual(project.base_url, "http://127.0.0.1:8003")
        self.assertEqual(project.description, "Another running web app")

    def test_project_is_preselected_when_creating_its_test(self):
        response = self.client.get(
            reverse("create_test_case"), {"project": self.project.pk}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'value="{self.project.pk}" selected')

    def test_manual_result_endpoint_rejects_get_requests(self):
        response = self.client.get(
            reverse("record_manual_run", args=[self.manual_case.pk])
        )

        self.assertEqual(response.status_code, 405)
        self.assertFalse(TestRun.objects.filter(test_case=self.manual_case).exists())

    def test_invalid_manual_status_does_not_create_a_run(self):
        response = self.client.post(
            reverse("record_manual_run", args=[self.manual_case.pk]),
            {"status": "UNKNOWN", "actual_result": "not a supported result"},
        )

        self.assertRedirects(
            response, reverse("test_detail", args=[self.manual_case.pk])
        )
        self.assertFalse(TestRun.objects.filter(test_case=self.manual_case).exists())

    def test_manual_result_is_saved_to_run_history(self):
        response = self.client.post(
            reverse("record_manual_run", args=[self.manual_case.pk]),
            {
                "status": "FAIL",
                "actual_result": "The profile page displayed an error.",
            },
        )

        self.assertRedirects(
            response, reverse("test_detail", args=[self.manual_case.pk])
        )
        run = TestRun.objects.get(test_case=self.manual_case)
        self.assertEqual(run.status, "FAIL")
        self.assertEqual(
            run.actual_result, "The profile page displayed an error."
        )

    def test_bug_can_be_created_and_updated(self):
        create_response = self.client.post(
            reverse("create_bug"),
            {
                "project": str(self.project.pk),
                "title": "Profile page shows an error",
                "severity": "Medium",
                "status": "Open",
                "steps_to_reproduce": "Open the profile page",
                "expected_result": "The profile page is displayed",
                "actual_result": "An error message is displayed",
                "environment": "Local test environment",
            },
        )
        bug = BugReport.objects.get(title="Profile page shows an error")
        self.assertRedirects(
            create_response, reverse("bug_detail", args=[bug.pk])
        )

        edit_response = self.client.post(
            reverse("edit_bug", args=[bug.pk]),
            {
                "project": str(self.project.pk),
                "title": bug.title,
                "severity": "High",
                "status": "In Progress",
                "steps_to_reproduce": bug.steps_to_reproduce,
                "expected_result": bug.expected_result,
                "actual_result": bug.actual_result,
                "environment": bug.environment,
            },
        )
        self.assertRedirects(edit_response, reverse("bug_detail", args=[bug.pk]))
        bug.refresh_from_db()
        self.assertEqual(bug.severity, "High")
        self.assertEqual(bug.status, "In Progress")

    def test_health_endpoint_returns_service_status(self):
        response = self.client.get(reverse("api_health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok", "service": "BugPilot API", "version": "1.1"},
        )


class DeleteFlowTests(DjangoTestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Delete-flow project",
            base_url="http://127.0.0.1:8002",
        )
        self.test_case = TestCase.objects.create(
            project=self.project,
            title="Can be removed",
            test_type="manual",
            expected_result="It works",
        )
        self.run = TestRun.objects.create(
            test_case=self.test_case,
            status="FAIL",
            actual_result="Example failure",
        )
        self.bug = BugReport.objects.create(
            project=self.project,
            title="Delete-flow bug",
            steps_to_reproduce="Open the affected page",
            expected_result="The page is displayed",
            actual_result="An error is displayed",
        )

    def test_project_delete_requires_matching_name_and_removes_linked_records(self):
        url = reverse("delete_project", args=[self.project.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "type the project name")

        response = self.client.post(url, {"confirm_name": "different name"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())

        response = self.client.post(url, {"confirm_name": self.project.name})
        self.assertRedirects(response, reverse("project_list"))
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())
        self.assertFalse(TestCase.objects.filter(pk=self.test_case.pk).exists())
        self.assertFalse(TestRun.objects.filter(pk=self.run.pk).exists())
        self.assertFalse(BugReport.objects.filter(pk=self.bug.pk).exists())

    def test_test_case_delete_requires_confirmation_and_removes_its_runs(self):
        url = reverse("delete_test_case", args=[self.test_case.pk])

        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(TestCase.objects.filter(pk=self.test_case.pk).exists())

        response = self.client.post(url, {"confirm_delete": "yes"})
        self.assertRedirects(response, reverse("test_list"))
        self.assertFalse(TestCase.objects.filter(pk=self.test_case.pk).exists())
        self.assertFalse(TestRun.objects.filter(pk=self.run.pk).exists())

    def test_run_and_bug_can_be_deleted_individually(self):
        response = self.client.post(
            reverse("delete_run", args=[self.run.pk]),
            {"confirm_delete": "yes"},
        )
        self.assertRedirects(response, reverse("run_list"))
        self.assertFalse(TestRun.objects.filter(pk=self.run.pk).exists())
        self.assertTrue(TestCase.objects.filter(pk=self.test_case.pk).exists())

        response = self.client.post(
            reverse("delete_bug", args=[self.bug.pk]),
            {"confirm_delete": "yes"},
        )
        self.assertRedirects(response, reverse("bug_list"))
        self.assertFalse(BugReport.objects.filter(pk=self.bug.pk).exists())
        self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())

    def test_delete_endpoints_reject_methods_other_than_get_and_post(self):
        urls = [
            reverse("delete_project", args=[self.project.pk]),
            reverse("delete_test_case", args=[self.test_case.pk]),
            reverse("delete_run", args=[self.run.pk]),
            reverse("delete_bug", args=[self.bug.pk]),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.put(url)
                self.assertEqual(response.status_code, 405)

        self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())
        self.assertTrue(TestCase.objects.filter(pk=self.test_case.pk).exists())
        self.assertTrue(TestRun.objects.filter(pk=self.run.pk).exists())
        self.assertTrue(BugReport.objects.filter(pk=self.bug.pk).exists())


class ZipImportTests(DjangoTestCase):
    @staticmethod
    def make_zip(entries):
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, content in entries.items():
                archive.writestr(name, content)
        return output.getvalue()

    def test_zip_is_imported_without_running_its_code(self):
        marker = Path(settings.BASE_DIR) / "zip_payload_executed.txt"
        marker.unlink(missing_ok=True)
        self.addCleanup(marker.unlink, missing_ok=True)
        payload = (
            "from pathlib import Path\n"
            f"Path({str(marker)!r}).write_text('executed')\n"
        )
        zip_data = self.make_zip(
            {
                "sample_app/README.md": "Run this app locally",
                "sample_app/payload.py": payload,
            }
        )
        response = self.client.post(
            reverse("upload_project_zip"),
            {
                "name": "Sample App",
                "description": "Imported source code",
                "archive": SimpleUploadedFile(
                    "sample_app.zip", zip_data, content_type="application/zip"
                ),
            },
        )

        project = Project.objects.get(name="Sample App")
        self.assertRedirects(response, reverse("project_detail", args=[project.pk]))
        self.assertEqual(project.base_url, "")
        self.assertEqual(project.source_archive, "sample_app.zip")

        source_dir = Path(settings.BASE_DIR) / project.source_directory
        self.addCleanup(shutil.rmtree, source_dir, ignore_errors=True)
        self.assertTrue((source_dir / "sample_app" / "README.md").is_file())
        self.assertTrue((source_dir / "sample_app" / "payload.py").is_file())
        self.assertFalse(marker.exists())
        self.assertContains(
            self.client.get(reverse("project_detail", args=[project.pk])),
            "URL not set yet",
        )

    def test_unsafe_zip_paths_are_rejected(self):
        unsafe_paths = ["../escaped.txt", r"..\escaped.txt"]
        for index, unsafe_path in enumerate(unsafe_paths):
            with self.subTest(path=unsafe_path):
                zip_data = self.make_zip({unsafe_path: "must not be extracted"})
                project_name = f"Unsafe project {index}"
                response = self.client.post(
                    reverse("upload_project_zip"),
                    {
                        "name": project_name,
                        "archive": SimpleUploadedFile(
                            "unsafe.zip", zip_data, content_type="application/zip"
                        ),
                    },
                )

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "unsafe file path")
                self.assertFalse(Project.objects.filter(name=project_name).exists())

    def test_duplicate_paths_are_rejected_case_insensitively(self):
        zip_data = self.make_zip(
            {
                "README.md": "first file",
                "readme.md": "duplicate on case-insensitive filesystems",
            }
        )
        response = self.client.post(
            reverse("upload_project_zip"),
            {
                "name": "Duplicate archive",
                "archive": SimpleUploadedFile(
                    "duplicate.zip", zip_data, content_type="application/zip"
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "duplicate file paths")
        self.assertFalse(Project.objects.filter(name="Duplicate archive").exists())

    def test_symbolic_link_entries_are_rejected(self):
        output = io.BytesIO()
        link = zipfile.ZipInfo("sample_link")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        with zipfile.ZipFile(output, "w") as archive:
            archive.writestr(link, "../../outside.txt")

        response = self.client.post(
            reverse("upload_project_zip"),
            {
                "name": "Symlink archive",
                "archive": SimpleUploadedFile(
                    "symlink.zip", output.getvalue(), content_type="application/zip"
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "symbolic link")
        self.assertFalse(Project.objects.filter(name="Symlink archive").exists())

    def test_invalid_zip_is_rejected(self):
        response = self.client.post(
            reverse("upload_project_zip"),
            {
                "name": "Invalid archive",
                "archive": SimpleUploadedFile(
                    "invalid.zip", b"this is not a zip", content_type="application/zip"
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "not a valid ZIP archive")
        self.assertFalse(Project.objects.filter(name="Invalid archive").exists())

    def test_deleting_imported_project_removes_extracted_source(self):
        zip_data = self.make_zip({"README.md": "Imported source"})
        self.client.post(
            reverse("upload_project_zip"),
            {
                "name": "Disposable import",
                "archive": SimpleUploadedFile(
                    "disposable.zip", zip_data, content_type="application/zip"
                ),
            },
        )
        project = Project.objects.get(name="Disposable import")
        source_dir = Path(settings.BASE_DIR) / project.source_directory
        self.addCleanup(shutil.rmtree, source_dir, ignore_errors=True)
        self.assertTrue((source_dir / "README.md").exists())

        response = self.client.post(
            reverse("delete_project", args=[project.pk]),
            {"confirm_name": project.name},
        )
        self.assertRedirects(response, reverse("project_list"))
        self.assertFalse(source_dir.exists())

    def test_http_test_rejects_malformed_url_like_paths(self):
        project = Project.objects.create(
            name="Malformed path project",
            base_url="http://127.0.0.1:8002",
        )
        response = self.client.post(
            reverse("create_test_case"),
            {
                "project": str(project.pk),
                "title": "Malformed URL path",
                "test_type": "http",
                "steps": "Run the check",
                "expected_result": "The endpoint responds",
                "path": "http://[",
                "expected_status": "200",
                "expected_text": "",
                "is_active": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "valid relative path")
        self.assertFalse(TestCase.objects.filter(title="Malformed URL path").exists())

    def test_http_test_rejects_absolute_urls_as_paths(self):
        project = Project.objects.create(
            name="Path validation project",
            base_url="http://127.0.0.1:8002",
        )
        response = self.client.post(
            reverse("create_test_case"),
            {
                "project": str(project.pk),
                "title": "External URL path",
                "test_type": "http",
                "preconditions": "",
                "steps": "Run the HTTP check",
                "expected_result": "The endpoint responds",
                "path": "https://other.example/private",
                "expected_status": "200",
                "expected_text": "",
                "is_active": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter a relative path")
        self.assertFalse(TestCase.objects.filter(title="External URL path").exists())

    def test_http_test_requires_a_project_url(self):
        project = Project.objects.create(
            name="Source only", base_url="", source_archive="source.zip"
        )
        response = self.client.post(
            reverse("create_test_case"),
            {
                "project": str(project.pk),
                "title": "HTTP without URL",
                "test_type": "http",
                "preconditions": "",
                "steps": "Open endpoint",
                "expected_result": "Status 200",
                "path": "/",
                "expected_status": "200",
                "expected_text": "",
                "is_active": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "has no URL yet")
        self.assertFalse(TestCase.objects.filter(title="HTTP without URL").exists())


class HttpRunnerTests(DjangoTestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="HTTP test project",
            base_url="http://example.test",
        )
        self.test_case = TestCase.objects.create(
            project=self.project,
            title="Login page responds",
            test_type="http",
            path="/accounts/login/",
            expected_status=200,
            expected_text="Login",
        )

    def test_matching_status_and_text_are_saved_as_pass(self):
        response = Mock(status_code=200, text="Login form")
        with patch("qa.services.requests.get", return_value=response) as get:
            run = run_http_test(self.test_case)

        self.assertEqual(run.status, "PASS")
        self.assertIn("Actual status: 200", run.actual_result)
        get.assert_called_once_with(
            "http://example.test/accounts/login/",
            timeout=8,
            allow_redirects=False,
        )

    def test_status_or_expected_text_mismatch_is_saved_as_fail(self):
        response = Mock(status_code=404, text="Page not found")
        with patch("qa.services.requests.get", return_value=response):
            run = run_http_test(self.test_case)

        self.assertEqual(run.status, "FAIL")
        self.assertIn("Actual status: 404", run.actual_result)
        self.assertIn("Text found: False", run.actual_result)

    def test_request_error_is_saved_as_error(self):
        with patch(
            "qa.services.requests.get",
            side_effect=requests.Timeout("request timed out"),
        ):
            run = run_http_test(self.test_case)

        self.assertEqual(run.status, "ERROR")
        self.assertIn("Timeout", run.actual_result)

    def test_absolute_path_cannot_override_the_project_host(self):
        self.test_case.path = "https://other.example/private"
        with patch("qa.services.requests.get") as get:
            run = run_http_test(self.test_case)

        self.assertEqual(run.status, "ERROR")
        self.assertIn("must be relative", run.actual_result)
        get.assert_not_called()

    def test_external_redirect_is_not_followed(self):
        response = Mock(status_code=302, text="", headers={"Location": "https://other.example/"})
        with patch("qa.services.requests.get", return_value=response) as get:
            run = run_http_test(self.test_case)

        self.assertEqual(run.status, "FAIL")
        self.assertIn("Actual status: 302", run.actual_result)
        get.assert_called_once_with(
            "http://example.test/accounts/login/",
            timeout=8,
            allow_redirects=False,
        )

    def test_project_url_with_embedded_credentials_is_rejected(self):
        self.project.base_url = "https://qa:secret@example.test"
        self.project.save(update_fields=["base_url"])

        with patch("qa.services.requests.get") as get:
            run = run_http_test(self.test_case)

        self.assertEqual(run.status, "ERROR")
        self.assertIn("embedded credentials", run.actual_result)
        get.assert_not_called()

    def test_test_without_base_url_is_saved_as_error_without_request(self):
        self.project.base_url = ""
        self.project.save(update_fields=["base_url"])

        with patch("qa.services.requests.get") as get:
            run = run_http_test(self.test_case)

        self.assertEqual(run.status, "ERROR")
        get.assert_not_called()


class SeedDemoCommandTests(DjangoTestCase):
    def test_seed_command_is_repeatable_and_preserves_other_projects(self):
        unrelated_project = Project.objects.create(
            name="My separate app",
            base_url="http://127.0.0.1:8010",
        )
        unrelated_case = TestCase.objects.create(
            project=unrelated_project,
            title="My own regression case",
            expected_result="The page opens",
        )

        call_command("seed_demo", stdout=StringIO())
        call_command("seed_demo", stdout=StringIO())

        sample_project = Project.objects.get(name="Task Management System")
        self.assertEqual(sample_project.base_url, "http://127.0.0.1:8001")
        self.assertEqual(sample_project.test_cases.count(), 10)
        self.assertEqual(
            sample_project.test_cases.values("title").distinct().count(), 10
        )
        self.assertTrue(
            TestCase.objects.filter(
                pk=unrelated_case.pk,
                project=unrelated_project,
                title="My own regression case",
            ).exists()
        )
        self.assertEqual(Project.objects.count(), 2)
