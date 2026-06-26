from django.urls import path
from .views import health, analyze_ticket

urlpatterns = [
    path("health", health),
    path("health/", health),

    path("analyze-ticket", analyze_ticket),
    path("analyze-ticket/", analyze_ticket),
]