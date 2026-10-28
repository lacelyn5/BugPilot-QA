from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=120)
    base_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    source_directory = models.CharField(max_length=500, blank=True)
    source_archive = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class TestCase(models.Model):
    TYPE_CHOICES = [
        ("manual", "Manual"),
        ("http", "HTTP automated"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="test_cases",
    )
    title = models.CharField(max_length=180)
    test_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="manual")
    preconditions = models.TextField(blank=True)
    steps = models.TextField(blank=True)
    expected_result = models.TextField()
    path = models.CharField(max_length=255, blank=True)
    expected_status = models.PositiveIntegerField(default=200)
    expected_text = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.project.name}: {self.title}"


class TestRun(models.Model):
    STATUS_CHOICES = [
        ("PASS", "PASS"),
        ("FAIL", "FAIL"),
        ("ERROR", "ERROR"),
    ]

    test_case = models.ForeignKey(
        TestCase,
        on_delete=models.CASCADE,
        related_name="runs",
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    actual_result = models.TextField()
    duration_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class BugReport(models.Model):
    SEVERITY = [
        ("Low", "Low"),
        ("Medium", "Medium"),
        ("High", "High"),
        ("Critical", "Critical"),
    ]
    STATUS = [
        ("Open", "Open"),
        ("In Progress", "In Progress"),
        ("Ready for Retest", "Ready for Retest"),
        ("Closed", "Closed"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="bugs",
    )
    title = models.CharField(max_length=180)
    severity = models.CharField(max_length=20, choices=SEVERITY, default="Medium")
    status = models.CharField(max_length=30, choices=STATUS, default="Open")
    steps_to_reproduce = models.TextField()
    expected_result = models.TextField()
    actual_result = models.TextField()
    environment = models.CharField(max_length=180, default="Windows 11 / Chrome")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"BUG-{self.pk}: {self.title}"
