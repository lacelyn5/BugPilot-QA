from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Task

User = get_user_model()


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "priority", "due_date", "is_completed"]
        labels = {
            "title": "Task title",
            "description": "Description",
            "priority": "Priority",
            "due_date": "Due date",
            "is_completed": "Completed",
        }
        widgets = {
            "title": forms.TextInput(
                attrs={"placeholder": "Enter task title", "class": "form-control"}
            ),
            "description": forms.Textarea(
                attrs={
                    "placeholder": "Describe the task",
                    "rows": 4,
                    "class": "form-control",
                }
            ),
            "priority": forms.Select(attrs={"class": "form-control"}),
            "due_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
        }


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
        labels = {
            "username": "Username",
            "email": "Email",
            "password1": "Password",
            "password2": "Confirm password",
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email
