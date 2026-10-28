from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("guide/", views.guide, name="guide"),
    path("projects/", views.project_list, name="project_list"),
    path("projects/new/", views.create_project, name="create_project"),
    path("projects/upload/", views.upload_project_zip, name="upload_project_zip"),
    path("projects/<int:pk>/", views.project_detail, name="project_detail"),
    path("projects/<int:pk>/edit/", views.edit_project, name="edit_project"),
    path("projects/<int:pk>/delete/", views.delete_project, name="delete_project"),
    path("tests/", views.test_list, name="test_list"),
    path("tests/new/", views.create_test_case, name="create_test_case"),
    path("tests/<int:pk>/", views.test_detail, name="test_detail"),
    path("tests/<int:pk>/edit/", views.edit_test_case, name="edit_test_case"),
    path("tests/<int:pk>/delete/", views.delete_test_case, name="delete_test_case"),
    path("tests/<int:pk>/run/", views.run_test, name="run_test"),
    path("tests/<int:pk>/record/", views.record_manual_run, name="record_manual_run"),
    path("runs/", views.run_list, name="run_list"),
    path("runs/<int:pk>/delete/", views.delete_run, name="delete_run"),
    path("bugs/", views.bug_list, name="bug_list"),
    path("bugs/new/", views.create_bug, name="create_bug"),
    path("bugs/<int:pk>/edit/", views.edit_bug, name="edit_bug"),
    path("bugs/<int:pk>/delete/", views.delete_bug, name="delete_bug"),
    path("bugs/<int:pk>/", views.bug_detail, name="bug_detail"),
]
