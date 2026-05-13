from django.urls import path

from .api_views import DashboardSummaryAPIView, EmailAssistantAPIView


urlpatterns = [
    path('summary/', DashboardSummaryAPIView.as_view(), name='dashboard-summary'),
    path(
        'email-assistant/',
        EmailAssistantAPIView.as_view(),
        name='dashboard-email-assistant',
    ),
]
