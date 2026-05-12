from rest_framework.response import Response
from rest_framework.views import APIView

from leads.models import Agent, Category, Lead


class DashboardSummaryAPIView(APIView):
    def get(self, request):
        return Response({
            'total_leads': Lead.objects.count(),
            'total_categories': Category.objects.count(),
            'total_agents': Agent.objects.count(),
            'new_leads': Lead.objects.filter(status=Lead.STATUS_NEW).count(),
            'converted_leads': Lead.objects.filter(
                status=Lead.STATUS_CONVERTED
            ).count(),
        })
