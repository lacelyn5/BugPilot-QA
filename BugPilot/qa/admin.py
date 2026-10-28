from django.contrib import admin

from .models import BugReport, Project, TestCase, TestRun


admin.site.register(Project)
admin.site.register(TestCase)
admin.site.register(TestRun)
admin.site.register(BugReport)
