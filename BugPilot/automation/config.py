"""Environment-based URLs and credentials for the browser test suite."""

import os


BUGPILOT_URL = os.getenv("BUGPILOT_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
TASK_MANAGER_URL = os.getenv(
    "TASK_MANAGER_BASE_URL", "http://127.0.0.1:8001"
).rstrip("/")
QA_USERNAME = os.getenv("QA_USERNAME", "qa_user")
QA_PASSWORD = os.getenv("QA_PASSWORD", "QApass123!")
