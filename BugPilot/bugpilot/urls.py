from django.contrib import admin
from django.urls import include, path

from qa.views import api_health


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", api_health, name="api_health"),
    path("", include("qa.urls")),
]
