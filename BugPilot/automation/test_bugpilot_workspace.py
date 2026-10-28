"""End-to-end checks for BugPilot's core user workflows."""

from uuid import uuid4

import pytest

from .config import BUGPILOT_URL


def test_dashboard_shows_main_sections(page):
    response = page.goto(BUGPILOT_URL)

    assert response is not None and response.status == 200
    assert page.get_by_role("heading", name="Quality dashboard").is_visible()
    for section in ["Projects", "Test cases", "Run history", "Bug reports", "How to use"]:
        assert page.get_by_role("link", name=section, exact=True).is_visible()


def test_project_can_be_created_and_deleted_from_the_interface(page):
    project_name = f"E2E Temporary Project {uuid4().hex[:8]}"
    page.goto(f"{BUGPILOT_URL}/projects/")
    page.get_by_role("link", name="Add project").click()
    page.fill("#id_name", project_name)
    page.fill("#id_base_url", "http://127.0.0.1:8999")
    page.fill("#id_description", "Temporary project created by a browser test.")
    page.get_by_role("button", name="Save").click()

    assert page.get_by_role("heading", name=project_name, exact=True).is_visible()
    page.locator(".page-heading .actions").get_by_role(
        "link", name="Delete", exact=True
    ).click()
    page.fill("#confirm-name", project_name)
    page.get_by_role("button", name="Delete permanently").click()

    assert page.get_by_role("heading", name="Projects").is_visible()
    assert page.get_by_role("link", name=project_name, exact=True).count() == 0


@pytest.mark.parametrize(
    "case_title",
    ["Login page is available", "Registration page is available"],
)
def test_http_smoke_case_returns_pass(page, case_title):
    """Run the built-in HTTP check against the live TaskManager app."""
    page.goto(f"{BUGPILOT_URL}/tests/")
    page.get_by_role("link", name=case_title, exact=True).click()
    page.get_by_role("button", name="Run check now").click()

    latest_result = page.locator("article.run-card").first
    assert latest_result.get_by_text("PASS", exact=True).is_visible()
    assert "Actual status: 200" in latest_result.inner_text()


def test_manual_test_result_is_saved_and_can_be_removed(page):
    note = f"Browser test evidence {uuid4().hex[:8]}"
    page.goto(f"{BUGPILOT_URL}/tests/")
    page.get_by_role(
        "link", name="Unauthenticated user is redirected to login", exact=True
    ).click()
    page.locator("#actual-result").fill(note)
    page.get_by_role("button", name="✓ Mark PASS").click()

    run_card = page.locator("article.run-card").filter(has_text=note)
    assert run_card.get_by_text("PASS", exact=True).is_visible()
    assert note in run_card.inner_text()

    run_card.get_by_role("link", name="Delete this result").click()
    page.locator('input[name="confirm_delete"]').check()
    page.get_by_role("button", name="Delete permanently").click()
    assert page.get_by_text(note, exact=True).count() == 0


def test_bug_report_can_be_created_updated_and_deleted(page):
    bug_title = f"E2E bug report {uuid4().hex[:8]}"
    page.goto(f"{BUGPILOT_URL}/bugs/new/")
    page.select_option("#id_project", label="Task Management System")
    page.fill("#id_title", bug_title)
    page.select_option("#id_severity", "Medium")
    page.select_option("#id_status", "Open")
    page.fill("#id_steps_to_reproduce", "1. Open the page.\n2. Observe the error.")
    page.fill("#id_expected_result", "The page should load without an error.")
    page.fill("#id_actual_result", "The page displays an unexpected error.")
    page.fill("#id_environment", "Playwright / Chromium")
    page.get_by_role("button", name="Save").click()

    assert page.get_by_role("heading", name=bug_title, exact=True).is_visible()
    page.get_by_role("link", name="Edit bug / update status").click()
    page.select_option("#id_severity", "High")
    page.select_option("#id_status", "In Progress")
    page.get_by_role("button", name="Save").click()

    assert page.get_by_text("High", exact=True).is_visible()
    assert page.get_by_text("In Progress", exact=True).is_visible()
    page.get_by_role("link", name="Delete bug").click()
    page.locator('input[name="confirm_delete"]').check()
    page.get_by_role("button", name="Delete permanently").click()
    assert page.get_by_role("heading", name="Bug reports").is_visible()
    assert page.get_by_text(bug_title, exact=True).count() == 0


def test_guide_explains_safe_zip_import(page):
    response = page.goto(f"{BUGPILOT_URL}/guide/")

    assert response is not None and response.status == 200
    assert page.get_by_role("heading", name="How to use BugPilot").is_visible()
    assert page.get_by_role(
        "heading", name="Import another project's ZIP"
    ).is_visible()
    assert page.get_by_text(
        "does not execute code from an uploaded archive", exact=False
    ).is_visible()
