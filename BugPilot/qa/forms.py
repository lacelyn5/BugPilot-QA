from urllib.parse import urlsplit

from django import forms

from .models import BugReport, Project, TestCase


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "base_url", "description"]
        widgets = {
            "name": forms.TextInput(
                attrs={"placeholder": "e.g. Storefront application"}
            ),
            "base_url": forms.URLInput(
                attrs={"placeholder": "http://127.0.0.1:8001"}
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "What is this application used for?",
                }
            ),
        }
        help_texts = {
            "base_url": (
                "Optional during setup. Use an HTTP or HTTPS base URL without "
                "credentials, query parameters or a fragment."
            ),
        }

    def clean_base_url(self):
        value = self.cleaned_data.get("base_url", "").strip()
        if not value:
            return ""

        try:
            parts = urlsplit(value)
        except ValueError as exc:
            raise forms.ValidationError("Enter a valid HTTP or HTTPS URL.") from exc
        if parts.scheme.lower() not in {"http", "https"} or not parts.netloc:
            raise forms.ValidationError("Enter a valid HTTP or HTTPS URL.")
        if parts.username or parts.password:
            raise forms.ValidationError(
                "Do not put login credentials in the project URL."
            )
        if parts.query or parts.fragment:
            raise forms.ValidationError(
                "Enter the base address only; query parameters and fragments are not allowed."
            )
        return value.rstrip("/")


class UploadProjectZipForm(forms.Form):
    name = forms.CharField(
        max_length=120,
        required=False,
        label="Project name",
        help_text="Optional. Leave blank to use the ZIP file name.",
    )
    description = forms.CharField(
        required=False,
        label="Description",
        widget=forms.Textarea(
            attrs={"rows": 3, "placeholder": "What does this project do?"}
        ),
    )
    archive = forms.FileField(
        label="Project ZIP file",
        help_text=(
            "ZIP archives up to 20 MB. The files are imported but never run "
            "automatically."
        ),
    )

    def clean_archive(self):
        archive = self.cleaned_data["archive"]
        if not archive.name.lower().endswith(".zip"):
            raise forms.ValidationError("Choose a .zip archive.")
        if archive.size > 20 * 1024 * 1024:
            raise forms.ValidationError("The ZIP file must be 20 MB or smaller.")
        return archive

    def clean_name(self):
        return self.cleaned_data.get("name", "").strip()


class TestCaseForm(forms.ModelForm):
    class Meta:
        model = TestCase
        fields = [
            "project",
            "title",
            "test_type",
            "preconditions",
            "steps",
            "expected_result",
            "path",
            "expected_status",
            "expected_text",
            "is_active",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={"placeholder": "e.g. User can open the profile page"}
            ),
            "preconditions": forms.Textarea(attrs={"rows": 2}),
            "steps": forms.Textarea(attrs={"rows": 5}),
            "expected_result": forms.Textarea(attrs={"rows": 3}),
            "path": forms.TextInput(
                attrs={"placeholder": "/login/ or /api/health/"}
            ),
            "expected_text": forms.TextInput(
                attrs={"placeholder": "Optional text expected in the response"}
            ),
        }
        help_texts = {
            "test_type": (
                "HTTP checks send one GET request to the project's base URL "
                "plus a relative path. Redirects are reported as returned; they "
                "are not followed automatically. Manual cases can be marked "
                "PASS / FAIL after you follow the steps."
            ),
            "path": (
                "Enter a path relative to the project's base URL, such as "
                "/login/ or /api/health/. Absolute URLs are not accepted."
            ),
        }

    def clean_path(self):
        value = self.cleaned_data.get("path", "").strip()
        normalized = value.replace("\\", "/")
        try:
            parts = urlsplit(normalized)
        except ValueError as exc:
            raise forms.ValidationError("Enter a valid relative path.") from exc
        if parts.scheme or parts.netloc or normalized.startswith("//"):
            raise forms.ValidationError(
                "Enter a relative path, not a complete URL or another host."
            )
        if any(ord(character) < 32 for character in value):
            raise forms.ValidationError("The path cannot contain control characters.")
        return value

    def clean(self):
        cleaned_data = super().clean()
        project = cleaned_data.get("project")
        test_type = cleaned_data.get("test_type")
        if project and test_type == "http" and not project.base_url:
            self.add_error(
                "project",
                "This project has no URL yet. Start the app and edit the "
                "project to add its URL before creating an HTTP test.",
            )
        return cleaned_data


class BugReportForm(forms.ModelForm):
    class Meta:
        model = BugReport
        fields = [
            "project",
            "title",
            "severity",
            "status",
            "steps_to_reproduce",
            "expected_result",
            "actual_result",
            "environment",
        ]
        widgets = {
            "steps_to_reproduce": forms.Textarea(attrs={"rows": 4}),
            "expected_result": forms.Textarea(attrs={"rows": 3}),
            "actual_result": forms.Textarea(attrs={"rows": 3}),
        }
