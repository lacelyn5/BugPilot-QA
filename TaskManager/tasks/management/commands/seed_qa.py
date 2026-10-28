from datetime import timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from tasks.models import Task


class Command(BaseCommand):
    help = "Create disposable QA users and sample data for browser testing"

    def handle(self, *args, **options):
        qa_user, _ = User.objects.get_or_create(
            username="qa_user",
            defaults={"email": "qa_user@example.com"},
        )
        qa_user.email = "qa_user@example.com"
        qa_user.set_password("QApass123!")
        qa_user.is_staff = False
        qa_user.save()

        other_user, _ = User.objects.get_or_create(
            username="qa_other",
            defaults={"email": "qa_other@example.com"},
        )
        other_user.email = "qa_other@example.com"
        other_user.set_password("OtherPass123!")
        other_user.is_staff = False
        other_user.save()

        Task.objects.filter(owner=qa_user).delete()
        Task.objects.filter(owner=other_user).delete()

        today = timezone.localdate()

        Task.objects.create(
            owner=qa_user,
            title="QA Baseline High Priority",
            description="Known task used for filter and search verification.",
            priority="high",
            is_completed=False,
            due_date=today + timedelta(days=30),
        )
        Task.objects.create(
            owner=qa_user,
            title="QA Completed Low Priority",
            description="Known completed task used for regression verification.",
            priority="low",
            is_completed=True,
            due_date=today + timedelta(days=31),
        )
        Task.objects.create(
            owner=other_user,
            title="PRIVATE OTHER USER TASK",
            description="This task must never appear for qa_user.",
            priority="medium",
            is_completed=False,
            due_date=today + timedelta(days=32),
        )

        self.stdout.write(self.style.SUCCESS(
            "QA seed ready: qa_user / QApass123! and isolated qa_other data."
        ))
