"""Execution services for BugPilot test cases."""

import time
from urllib.parse import urljoin, urlsplit

import requests

from .models import TestRun


HTTP_TIMEOUT_SECONDS = 8


def _save_error(test_case, started_at, message):
    duration_ms = int((time.perf_counter() - started_at) * 1000)
    return TestRun.objects.create(
        test_case=test_case,
        status="ERROR",
        actual_result=message,
        duration_ms=duration_ms,
    )


def _build_target_url(base_url, path):
    """Build a same-origin HTTP(S) URL without accepting absolute test paths."""
    base = urlsplit((base_url or "").strip())
    if base.scheme.lower() not in {"http", "https"} or not base.netloc:
        raise ValueError("The project URL must use HTTP or HTTPS.")
    if base.username or base.password:
        raise ValueError("The project URL must not contain embedded credentials.")
    if base.query or base.fragment:
        raise ValueError("The project URL must not contain a query or fragment.")

    relative_path = (path or "").strip().replace("\\", "/")
    candidate = urlsplit(relative_path)
    if candidate.scheme or candidate.netloc or relative_path.startswith("//"):
        raise ValueError("The test path must be relative to the project URL.")
    if any(ord(character) < 32 for character in relative_path):
        raise ValueError("The test path contains control characters.")

    target_url = urljoin(f"{base_url.rstrip('/')}/", relative_path.lstrip("/"))
    target = urlsplit(target_url)
    if (
        target.scheme.lower() != base.scheme.lower()
        or target.netloc.casefold() != base.netloc.casefold()
        or target.username
        or target.password
    ):
        raise ValueError("The test target must stay on the project's host.")
    return target_url


def run_http_test(test_case):
    """Run one bounded HTTP GET check and store the result in run history.

    Redirects are intentionally not followed. A test records the response from
    the exact configured endpoint, and cannot be redirected to another host.
    """
    started_at = time.perf_counter()
    base_url = test_case.project.base_url

    if not base_url:
        return _save_error(
            test_case,
            started_at,
            "This project has no base URL. Start the application, edit the "
            "project and add its URL before running this test.",
        )

    try:
        url = _build_target_url(base_url, test_case.path)
    except ValueError as exc:
        return _save_error(test_case, started_at, f"Invalid HTTP test target: {exc}")

    try:
        response = requests.get(
            url,
            timeout=HTTP_TIMEOUT_SECONDS,
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        actual_result = f"URL: {url}\nRequest failed: {type(exc).__name__}: {exc}"
        status = "ERROR"
    else:
        status_matches = response.status_code == test_case.expected_status
        text_matches = (
            not test_case.expected_text
            or test_case.expected_text.casefold() in response.text.casefold()
        )
        status = "PASS" if status_matches and text_matches else "FAIL"
        actual_result = "\n".join(
            [
                f"URL: {url}",
                f"Expected status: {test_case.expected_status}",
                f"Actual status: {response.status_code}",
                f"Expected text: {test_case.expected_text!r}",
                f"Text found: {text_matches}",
            ]
        )

    duration_ms = int((time.perf_counter() - started_at) * 1000)
    return TestRun.objects.create(
        test_case=test_case,
        status=status,
        actual_result=actual_result,
        duration_ms=duration_ms,
    )
