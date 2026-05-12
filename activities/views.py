from rest_framework import viewsets

from .models import Activity
from .serializers import ActivitySerializer


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.select_related('lead')
    serializer_class = ActivitySerializer
