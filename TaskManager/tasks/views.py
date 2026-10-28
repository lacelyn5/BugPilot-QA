from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import RegisterForm, TaskForm
from .models import Task


def _task_for_user(user, pk):
    """Return a task the current user is allowed to manage, or raise 404."""
    return get_object_or_404(Task, pk=pk, owner=user)


@login_required
def task_list(request):
    base_tasks = Task.objects.filter(owner=request.user)

    search_query = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "all")
    priority_filter = request.GET.get("priority", "all")

    tasks = base_tasks

    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    if status_filter == "completed":
        tasks = tasks.filter(is_completed=True)
    elif status_filter == "in_progress":
        tasks = tasks.filter(is_completed=False)

    if priority_filter in {"low", "medium", "high"}:
        tasks = tasks.filter(priority=priority_filter)

    context = {
        "tasks": tasks.order_by("due_date", "-id"),
        "total_tasks": base_tasks.count(),
        "completed_tasks": base_tasks.filter(is_completed=True).count(),
        "in_progress_tasks": base_tasks.filter(is_completed=False).count(),
        "search_query": search_query,
        "status_filter": status_filter,
        "priority_filter": priority_filter,
    }
    return render(request, "tasks/task_list.html", context)


@login_required
def task_create(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.owner = request.user
            task.save()
            return redirect("task_list")
    else:
        form = TaskForm()

    return render(request, "tasks/task_form.html", {"form": form})


@login_required
def task_update(request, pk):
    task = _task_for_user(request.user, pk)

    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect("task_list")
    else:
        form = TaskForm(instance=task)

    return render(request, "tasks/task_form.html", {"form": form})


@login_required
def task_delete(request, pk):
    task = _task_for_user(request.user, pk)

    if request.method == "POST":
        task.delete()
        return redirect("task_list")

    return render(request, "tasks/task_confirm_delete.html", {"task": task})


def register(request):
    if request.user.is_authenticated:
        return redirect("task_list")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("task_list")
    else:
        form = RegisterForm()

    return render(request, "tasks/register.html", {"form": form})
