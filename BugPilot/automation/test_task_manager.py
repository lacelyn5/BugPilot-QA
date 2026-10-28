"""Browser regression tests for the TaskManager application."""

from datetime import date, timedelta
from uuid import uuid4

from .config import TASK_MANAGER_URL


def create_task(page, *, priority="medium"):
    """Create a uniquely named task and return its title."""
    title = f"E2E Task {uuid4().hex[:8]}"
    page.get_by_role("link", name="+ Create Task").click()
    page.fill("#id_title", title)
    page.fill("#id_description", "Created by the TaskManager browser regression suite.")
    page.select_option("#id_priority", priority)
    page.fill("#id_due_date", (date.today() + timedelta(days=30)).isoformat())
    page.get_by_role("button", name="Save Task").click()
    page.get_by_role("heading", name=title, exact=True).wait_for()
    return title


def test_unauthenticated_dashboard_redirects_to_login(page):
    response = page.goto(f"{TASK_MANAGER_URL}/")

    assert response is not None and response.status == 200
    page.wait_for_url("**/accounts/login/?next=/")
    assert page.get_by_role("heading", name="Login").is_visible()


def test_valid_login_shows_only_the_users_own_tasks(logged_in_task_manager_page):
    page = logged_in_task_manager_page

    assert page.get_by_text("qa_user", exact=True).is_visible()
    assert page.get_by_role(
        "heading", name="QA Baseline High Priority", exact=True
    ).is_visible()
    assert page.get_by_role(
        "heading", name="PRIVATE OTHER USER TASK", exact=True
    ).count() == 0


def test_search_returns_matching_tasks(logged_in_task_manager_page):
    page = logged_in_task_manager_page

    page.fill('input[name="search"]', "Baseline")
    page.get_by_role("button", name="Apply").click()

    assert page.get_by_role(
        "heading", name="QA Baseline High Priority", exact=True
    ).is_visible()
    assert page.get_by_role(
        "heading", name="QA Completed Low Priority", exact=True
    ).count() == 0


def test_user_can_create_a_task(logged_in_task_manager_page):
    page = logged_in_task_manager_page
    title = create_task(page, priority="high")

    task_card = page.locator("article.task-card").filter(has_text=title)
    assert task_card.get_by_text("High priority", exact=True).is_visible()
    assert task_card.get_by_text("In progress", exact=True).is_visible()


def test_user_can_edit_and_complete_a_task(logged_in_task_manager_page):
    page = logged_in_task_manager_page
    original_title = create_task(page)
    task_card = page.locator("article.task-card").filter(has_text=original_title)
    task_card.get_by_role("link", name="Edit").click()

    updated_title = f"{original_title} Updated"
    page.fill("#id_title", updated_title)
    page.check("#id_is_completed")
    page.get_by_role("button", name="Save Task").click()

    updated_card = page.locator("article.task-card").filter(has_text=updated_title)
    assert updated_card.get_by_text("Completed", exact=True).is_visible()
    assert page.get_by_role("heading", name=original_title, exact=True).count() == 0


def test_priority_filter_shows_only_the_selected_priority(logged_in_task_manager_page):
    page = logged_in_task_manager_page

    page.select_option('select[name="priority"]', "high")
    page.get_by_role("button", name="Apply").click()

    cards = page.locator("article.task-card")
    assert cards.count() >= 1
    for index in range(cards.count()):
        assert "High priority" in cards.nth(index).inner_text()
    assert page.get_by_role(
        "heading", name="QA Completed Low Priority", exact=True
    ).count() == 0


def test_user_cannot_find_another_users_task(logged_in_task_manager_page):
    page = logged_in_task_manager_page

    page.fill('input[name="search"]', "PRIVATE OTHER USER TASK")
    page.get_by_role("button", name="Apply").click()

    assert page.get_by_role(
        "heading", name="PRIVATE OTHER USER TASK", exact=True
    ).count() == 0
    assert page.get_by_role("heading", name="No tasks found").is_visible()


def test_user_can_delete_own_task(logged_in_task_manager_page):
    page = logged_in_task_manager_page
    title = create_task(page)
    task_card = page.locator("article.task-card").filter(has_text=title)
    task_card.get_by_role("link", name="Delete").click()

    assert page.get_by_role("heading", name="Delete Task").is_visible()
    page.get_by_role("button", name="Yes, Delete").click()

    assert page.get_by_role("heading", name=title, exact=True).count() == 0
