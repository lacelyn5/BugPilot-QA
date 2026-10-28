from pathlib import Path
import zipfile
import zlib

from django.contrib import messages
from django.db.models import Count, OuterRef, Subquery
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from .archive_utils import (
    ProjectArchiveError,
    extract_project_archive,
    remove_project_source,
)
from .forms import (
    BugReportForm,
    ProjectForm,
    TestCaseForm,
    UploadProjectZipForm,
)
from .models import BugReport, Project, TestCase, TestRun
from .services import run_http_test


def _with_latest_run_status(test_cases):
    latest_run = TestRun.objects.filter(test_case=OuterRef("pk")).order_by(
        "-created_at", "-pk"
    )
    return test_cases.annotate(
        latest_run_status=Subquery(latest_run.values("status")[:1])
    )


def dashboard(request):
    projects = Project.objects.annotate(
        test_case_count=Count("test_cases", distinct=True),
        bug_count=Count("bugs", distinct=True),
    ).order_by("name")
    return render(request, "qa/dashboard.html", {
        "projects": projects,
        "test_cases": TestCase.objects.select_related("project").all()[:10],
        "recent_runs": TestRun.objects.select_related("test_case", "test_case__project")[:8],
        "bugs": BugReport.objects.select_related("project")[:8],
        "total_projects": projects.count(),
        "total_tests": TestCase.objects.count(),
        "pass_count": TestRun.objects.filter(status="PASS").count(),
        "fail_count": TestRun.objects.filter(status__in=["FAIL", "ERROR"]).count(),
        "open_bugs": BugReport.objects.exclude(status="Closed").count(),
    })


def project_list(request):
    projects = Project.objects.annotate(
        test_case_count=Count("test_cases", distinct=True),
        bug_count=Count("bugs", distinct=True),
    ).order_by("name")
    return render(request, "qa/project_list.html", {"projects": projects})


def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    test_cases = _with_latest_run_status(project.test_cases.all())
    runs = TestRun.objects.filter(test_case__project=project).select_related("test_case")[:10]
    bugs = project.bugs.all()
    return render(request, "qa/project_detail.html", {
        "project": project,
        "test_cases": test_cases,
        "recent_runs": runs,
        "bugs": bugs,
        "total_tests": test_cases.count(),
        "passed_runs": TestRun.objects.filter(test_case__project=project, status="PASS").count(),
        "failed_runs": TestRun.objects.filter(
            test_case__project=project,
            status__in=["FAIL", "ERROR"],
        ).count(),
        "open_bugs": bugs.exclude(status="Closed").count(),
    })


def test_list(request):
    projects = Project.objects.all().order_by("name")
    selected_project = None
    project_value = request.GET.get("project", "")
    test_cases = _with_latest_run_status(
        TestCase.objects.select_related("project").all()
    )
    if project_value.isdigit():
        selected_project = Project.objects.filter(pk=int(project_value)).first()
        if selected_project:
            test_cases = test_cases.filter(project=selected_project)
    return render(request, "qa/test_list.html", {
        "test_cases": test_cases,
        "projects": projects,
        "selected_project": selected_project,
    })


def run_list(request):
    runs = TestRun.objects.select_related("test_case", "test_case__project").all()[:100]
    return render(request, "qa/run_list.html", {"runs": runs})


def bug_list(request):
    bugs = BugReport.objects.select_related("project").all()
    project_value = request.GET.get("project", "")
    projects = Project.objects.all().order_by("name")
    selected_project = None
    if project_value.isdigit():
        selected_project = Project.objects.filter(pk=int(project_value)).first()
        if selected_project:
            bugs = bugs.filter(project=selected_project)
    return render(request, "qa/bug_list.html", {
        "bugs": bugs,
        "projects": projects,
        "selected_project": selected_project,
    })


def _form(request, form_class, title, instance=None, initial=None):
    form = form_class(request.POST or None, instance=instance, initial=initial)
    if request.method == "POST" and form.is_valid():
        saved = form.save()
        if isinstance(saved, Project):
            messages.success(request, "Project details saved.")
            return redirect("project_detail", pk=saved.pk)
        if isinstance(saved, BugReport):
            messages.success(request, "Bug report saved.")
            return redirect("bug_detail", pk=saved.pk)
        if isinstance(saved, TestCase):
            messages.success(request, "Test case saved.")
            return redirect("test_detail", pk=saved.pk)
        return redirect("dashboard")
    cancel_url = reverse("dashboard")
    if isinstance(instance, Project):
        cancel_url = reverse("project_detail", args=[instance.pk])
    elif isinstance(instance, TestCase):
        cancel_url = reverse("test_detail", args=[instance.pk])
    elif isinstance(instance, BugReport):
        cancel_url = reverse("bug_detail", args=[instance.pk])
    return render(request, "qa/form.html", {
        "form": form,
        "title": title,
        "object": instance,
        "cancel_url": cancel_url,
    })


def create_project(request):
    return _form(request, ProjectForm, "Add a project")


def edit_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    return _form(request, ProjectForm, f"Edit {project.name}", instance=project)


def upload_project_zip(request):
    form = UploadProjectZipForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        archive = form.cleaned_data["archive"]
        try:
            source_directory = extract_project_archive(archive)
        except ProjectArchiveError as exc:
            form.add_error("archive", str(exc))
        except (
            OSError,
            zipfile.BadZipFile,
            RuntimeError,
            ValueError,
            zlib.error,
            EOFError,
        ) as exc:
            form.add_error("archive", f"The ZIP could not be imported: {exc}")
        else:
            name = form.cleaned_data.get("name") or Path(archive.name).stem
            name = name.replace("_", " ").replace("-", " ").strip()
            name = name[:120] or "Imported project"
            try:
                project = Project.objects.create(
                    name=name,
                    base_url="",
                    description=form.cleaned_data.get("description", ""),
                    source_directory=source_directory,
                    source_archive=Path(archive.name).name[:255],
                )
            except Exception:
                # Do not leave orphaned source files if the database write fails.
                remove_project_source(source_directory)
                raise
            messages.success(
                request,
                "ZIP imported. Start the application separately, then edit "
                "the project to add its URL.",
            )
            return redirect("project_detail", pk=project.pk)
    return render(request, "qa/upload_project.html", {"form": form})


def create_test_case(request):
    initial = {}
    project_id = request.GET.get("project", "")
    if project_id.isdigit():
        project = Project.objects.filter(pk=int(project_id)).first()
        if project:
            initial["project"] = project
    return _form(request, TestCaseForm, "Create test case", initial=initial)


def edit_test_case(request, pk):
    test_case = get_object_or_404(TestCase.objects.select_related("project"), pk=pk)
    return _form(request, TestCaseForm, f"Edit TC-{test_case.pk:03d}", instance=test_case)


def create_bug(request):
    initial = {}
    project_id = request.GET.get("project", "")
    if project_id.isdigit():
        project = Project.objects.filter(pk=int(project_id)).first()
        if project:
            initial["project"] = project
    return _form(request, BugReportForm, "Report a bug", initial=initial)


def edit_bug(request, pk):
    bug = get_object_or_404(BugReport.objects.select_related("project"), pk=pk)
    return _form(request, BugReportForm, f"Edit BUG-{bug.pk:03d}", instance=bug)


def _confirm_delete(request, *, object_type, object_title, warning, cancel_url,
                    cancel_label="Cancel", confirmation_name=None, related_summary=""):
    context = {
        "object_type": object_type,
        "object_title": object_title,
        "warning": warning,
        "cancel_url": cancel_url,
        "cancel_label": cancel_label,
        "confirmation_name": confirmation_name,
        "related_summary": related_summary,
    }
    if request.method == "POST":
        if confirmation_name is not None:
            typed_name = request.POST.get("confirm_name", "").strip()
            if typed_name.casefold() != confirmation_name.casefold():
                context["error"] = "The name does not match. Nothing has been deleted."
                return render(request, "qa/confirm_delete.html", context)
        elif request.POST.get("confirm_delete") != "yes":
            context["error"] = "Confirm the checkbox to continue. Nothing has been deleted."
            return render(request, "qa/confirm_delete.html", context)
        return None
    return render(request, "qa/confirm_delete.html", context)


@require_http_methods(["GET", "POST"])
def delete_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    cancel_url = redirect("project_detail", pk=project.pk).url
    related_summary = (
        f"{project.test_cases.count()} test case(s), "
        f"{TestRun.objects.filter(test_case__project=project).count()} saved run(s), "
        f"and {project.bugs.count()} bug report(s)"
    )
    response = _confirm_delete(
        request,
        object_type="project",
        object_title=project.name,
        warning=(
            "Deleting this project also deletes its test cases, run history "
            "and bug reports. Imported source files will be removed too."
        ),
        cancel_url=cancel_url,
        confirmation_name=project.name,
        related_summary=related_summary,
    )
    if response is not None:
        return response
    source_directory = project.source_directory
    project_name = project.name
    project.delete()
    remove_project_source(source_directory)
    messages.success(request, f'Project “{project_name}” and its linked records were deleted.')
    return redirect("project_list")


@require_http_methods(["GET", "POST"])
def delete_test_case(request, pk):
    test_case = get_object_or_404(TestCase.objects.select_related("project"), pk=pk)
    cancel_url = redirect("test_detail", pk=test_case.pk).url
    response = _confirm_delete(
        request,
        object_type="test case",
        object_title=f"TC-{test_case.pk:03d} · {test_case.title}",
        warning="Deleting this test case also deletes every saved result in its run history.",
        cancel_url=cancel_url,
        related_summary=(
            f"Project: {test_case.project.name} · "
            f"{test_case.runs.count()} saved run(s)"
        ),
    )
    if response is not None:
        return response
    title = test_case.title
    test_case.delete()
    messages.success(request, f'Test case “{title}” and its run history were deleted.')
    return redirect("test_list")


@require_http_methods(["GET", "POST"])
def delete_run(request, pk):
    run = get_object_or_404(
        TestRun.objects.select_related("test_case", "test_case__project"),
        pk=pk,
    )
    cancel_url = redirect("run_list").url
    response = _confirm_delete(
        request,
        object_type="run result",
        object_title=f'{run.status} · {run.test_case.title}',
        warning=(
            "This removes only this saved execution result. The test case and "
            "its other results will remain."
        ),
        cancel_url=cancel_url,
        related_summary=(
            f"Project: {run.test_case.project.name} · "
            f"{run.created_at:%Y-%m-%d %H:%M:%S}"
        ),
    )
    if response is not None:
        return response
    run.delete()
    messages.success(request, "Run result deleted.")
    return redirect("run_list")


@require_http_methods(["GET", "POST"])
def delete_bug(request, pk):
    bug = get_object_or_404(BugReport.objects.select_related("project"), pk=pk)
    cancel_url = redirect("bug_detail", pk=bug.pk).url
    response = _confirm_delete(
        request,
        object_type="bug report",
        object_title=f"BUG-{bug.pk:03d} · {bug.title}",
        warning=(
            "This permanently deletes the bug report. The project and test "
            "history will remain unchanged."
        ),
        cancel_url=cancel_url,
        related_summary=(
            f"Project: {bug.project.name} · Severity: {bug.severity} · "
            f"Status: {bug.status}"
        ),
    )
    if response is not None:
        return response
    bug.delete()
    messages.success(request, "Bug report deleted.")
    return redirect("bug_list")


@require_POST
def run_test(request, pk):
    test_case = get_object_or_404(TestCase, pk=pk, is_active=True, test_type="http")
    run_http_test(test_case)
    return redirect("test_detail", pk=test_case.pk)


@require_POST
def record_manual_run(request, pk):
    test_case = get_object_or_404(TestCase, pk=pk, is_active=True, test_type="manual")
    status = request.POST.get("status", "").upper()
    allowed_statuses = {value for value, _label in TestRun.STATUS_CHOICES}
    if status not in allowed_statuses:
        messages.error(request, "Choose PASS, FAIL or ERROR to record a manual result.")
        return redirect("test_detail", pk=test_case.pk)
    actual_result = request.POST.get("actual_result", "").strip()
    if not actual_result:
        actual_result = {
            "PASS": "Manual test marked as passed.",
            "FAIL": "Manual test marked as failed. Add notes to describe the issue.",
            "ERROR": "Manual test could not be completed.",
        }[status]
    TestRun.objects.create(
        test_case=test_case,
        status=status,
        actual_result=actual_result,
        duration_ms=0,
    )
    messages.success(request, f"Manual result saved: {status}.")
    return redirect("test_detail", pk=test_case.pk)


def test_detail(request, pk):
    test_case = get_object_or_404(TestCase.objects.select_related("project"), pk=pk)
    return render(request, "qa/test_detail.html", {
        "test_case": test_case,
        "runs": test_case.runs.all()[:50],
    })


def bug_detail(request, pk):
    bug = get_object_or_404(BugReport.objects.select_related("project"), pk=pk)
    return render(request, "qa/bug_detail.html", {"bug": bug})


def guide(request):
    return render(request, "qa/guide.html")


def api_health(request):
    """Return a small response for a health check."""
    return JsonResponse(
        {"status": "ok", "service": "BugPilot API", "version": "1.1"}
    )
