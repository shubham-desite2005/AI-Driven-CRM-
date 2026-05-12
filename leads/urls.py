from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api_views import AgentViewSet, CategoryViewSet, LeadViewSet


router = DefaultRouter()
router.register('categories', CategoryViewSet, basename='category')
router.register('agents', AgentViewSet, basename='agent')
router.register('', LeadViewSet, basename='lead')

urlpatterns = [
    path('', include(router.urls)),
]
