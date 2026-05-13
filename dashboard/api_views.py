from rest_framework.response import Response
from rest_framework.views import APIView

from dashboard.services.email_assistant import get_gemini_email, send_email_message
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


class EmailAssistantAPIView(APIView):
    def post(self, request):
        action = request.data.get('action', 'generate')
        if action not in {'generate', 'fix_grammar', 'send'}:
            return Response(
                {'ok': False, 'message': 'Unsupported email assistant action.'},
                status=400,
            )

        if action == 'send':
            result = send_email_message(
                recipient=request.data.get('recipient', ''),
                email_body=request.data.get('email_body', ''),
            )
            return Response(result, status=200 if result.get('ok') else 400)

        lead = self._get_lead(request.data.get('lead_id'))
        result = get_gemini_email(
            action=action,
            lead=lead,
            recipient=request.data.get('recipient', ''),
            condition=request.data.get('condition', ''),
            email_body=request.data.get('email_body', ''),
        )
        return Response(result, status=200 if result.get('ok') else 400)

    def _get_lead(self, lead_id):
        queryset = Lead.objects.select_related('category', 'agent')
        if lead_id:
            try:
                return queryset.get(pk=lead_id)
            except (Lead.DoesNotExist, ValueError, TypeError):
                return None

        return queryset.order_by('-updated_at', '-id').first()
