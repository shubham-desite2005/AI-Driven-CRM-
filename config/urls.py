from django.contrib import admin
from django.urls import path, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('api/auth/', include('rest_framework.urls')),
    path('api/users/', include('users.urls')),
    path('api/leads/', include('leads.urls')),
    path('api/activities/', include('activities.urls')),
    path('api/dashboard/', include('dashboard.api_urls')),
    path('admin/', admin.site.urls),
]

urlpatterns += staticfiles_urlpatterns()
