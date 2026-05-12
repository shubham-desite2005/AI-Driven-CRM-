from rest_framework import viewsets

from .models import Agent, Category, Lead
from .serializers import AgentSerializer, CategorySerializer, LeadSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.order_by('name')
    serializer_class = CategorySerializer


class AgentViewSet(viewsets.ModelViewSet):
    queryset = Agent.objects.order_by('first_name', 'last_name')
    serializer_class = AgentSerializer


class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.select_related('category', 'agent').order_by('-id')
    serializer_class = LeadSerializer
