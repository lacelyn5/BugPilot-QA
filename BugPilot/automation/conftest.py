"""Shared browser-test configuration and failure screenshots."""

import re
from pathlib import Path

import pytest

from .config import QA_PASSWORD, QA_USERNAME, TASK_MANAGER_URL


SCREENSHOT_DIR = Path(__file__).resolve().parents[1] / "artifacts" / "screenshots"


@pytest.fixture
def logged_in_task_manager_page(page):
    """Open TaskManager as the disposable QA user created by seed_qa."""
    page.goto(f"{TASK_MANAGER_URL}/accounts/login/")
    page.fill("#id_username", QA_USERNAME)
    page.fill("#id_password", QA_PASSWORD)
    page.get_by_role("button", name="Login").click()
    page.wait_for_url(f"{TASK_MANAGER_URL}/")
    return page


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when != "call" or not report.failed:
        return

    page = item.funcargs.get("page")
    if page is None:
        page = item.funcargs.get("logged_in_task_manager_page")
    if page is None:
        return

    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", item.nodeid).strip("_")
    try:
        page.screenshot(path=str(SCREENSHOT_DIR / f"{safe_name}.png"), full_page=True)
    except Exception:
        # Screenshot capture must never replace the original test failure.
        pass
