from django.conf import settings


def workspace_environment(request):
    """Expose the configured environment label to the shared page layout."""
    return {"workspace_environment": settings.BUGPILOT_ENVIRONMENT}
