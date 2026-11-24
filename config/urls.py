from django.contrib import admin
from django.urls import include, path

from dashboard.views import dashboard, health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", dashboard, name="dashboard"),
    path("", include("accounts.urls")),
    path("", include("inventory.urls")),
    path("health/", health, name="health"),
]

handler404 = "config.views.page_not_found"
handler500 = "config.views.server_error"
