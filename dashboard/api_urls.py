from django.urls import path

from .api_views import DashboardSummaryAPIView


urlpatterns = [
    path('summary/', DashboardSummaryAPIView.as_view(), name='dashboard-summary'),
]
