from types import SimpleNamespace

from django.db.models import Count
from django.shortcuts import render
from django.views import generic
from accounts.mixins import RegularUserRequiredMixin
from dashboard.services.forecasting import (
    build_forecast_dataset,
    build_local_forecast,
    get_gemini_forecast,
)
from leads.models import Category, Lead


def _lead_priority_score(lead):
    category_name = (lead.category.name if lead.category else '').lower()
    score = 45 + min(lead.age, 45)

    if any(term in category_name for term in ['enterprise', 'vip', 'hot']):
        score += 20
    if getattr(lead, 'agent_id', None) or getattr(lead, 'agent', None):
        score += 8

    return min(score, 96)


def _lead_value(lead):
    return 45000 + (lead.age * 3500) + (lead.id * 9000)


def build_dashboard_context():
    leads = list(
        Lead.objects.select_related('category', 'agent').all().order_by('-id')
    )
    total_leads = len(leads)
    high_priority_count = sum(
        1 for lead in leads if _lead_priority_score(lead) >= 78
    )
    converted_count = max(2, round(total_leads * 0.24)) if total_leads else 0
    pending_followups = max(3, total_leads - converted_count - high_priority_count)
    revenue_forecast = sum(_lead_value(lead) for lead in leads[:12]) or 420000
    target_value = 800000
    target_progress = min(round((revenue_forecast / target_value) * 100), 100)

    category_counts = list(
        Category.objects.annotate(total=Count('lead')).order_by('-total')
        .values_list('name', 'total')
    )
    if not category_counts:
        category_counts = [
            ('Enterprise', 18),
            ('SMB', 24),
            ('Strategic', 9),
            ('Partner', 7),
        ]

    pipeline_stages = [
        ('New', 18),
        ('Contacted', 14),
        ('Negotiation', 9),
        ('Proposal', 7),
        ('Converted', converted_count or 5),
        ('Lost', 3),
    ]

    demo_leads = leads[:8] or [
        SimpleNamespace(
            first_name='Aarav',
            last_name='Mehta',
            email='aarav@acme.example',
            category=SimpleNamespace(name='Enterprise'),
            agent=SimpleNamespace(first_name='Priya'),
            age=32,
            id=1,
        ),
        SimpleNamespace(
            first_name='Nisha',
            last_name='Kapoor',
            email='nisha@northstar.example',
            category=SimpleNamespace(name='Strategic'),
            agent=SimpleNamespace(first_name='Rahul'),
            age=28,
            id=2,
        ),
    ]

    kanban = {
        'New': [],
        'Contacted': [],
        'Negotiation': [],
        'Proposal': [],
        'Converted': [],
        'Lost': [],
    }
    stage_names = list(kanban.keys())
    for index, lead in enumerate(demo_leads):
        score = _lead_priority_score(lead)
        stage = stage_names[index % len(stage_names)]
        company = (lead.email.split('@')[-1].split('.')[0] or 'client').title()
        kanban[stage].append({
            'name': f'{lead.first_name} {lead.last_name}',
            'company': f'{company} Corp',
            'value': f'₹{round(_lead_value(lead) / 100000, 1)}L',
            'priority': (
                'Critical' if score >= 86 else 'High' if score >= 74 else 'Warm'
            ),
            'probability': score,
        })

    return {
        'metrics': [
            {
                'label': 'Total Leads',
                'value': total_leads or 58,
                'trend': '+12.4%',
                'progress': 78,
                'icon': 'fa-users',
                'tone': 'cyan',
            },
            {
                'label': 'High Priority Leads',
                'value': high_priority_count or 11,
                'trend': '+8.1%',
                'progress': 64,
                'icon': 'fa-bolt',
                'tone': 'amber',
            },
            {
                'label': 'Converted Leads',
                'value': converted_count or 14,
                'trend': '+18.0%',
                'progress': 72,
                'icon': 'fa-circle-check',
                'tone': 'emerald',
            },
            {
                'label': 'Revenue Forecast',
                'value': f'₹{round(revenue_forecast / 100000, 1)}L',
                'trend': '+21.6%',
                'progress': target_progress,
                'icon': 'fa-chart-line',
                'tone': 'violet',
            },
            {
                'label': 'Monthly Target',
                'value': f'{target_progress}%',
                'trend': '+6.5%',
                'progress': target_progress,
                'icon': 'fa-bullseye',
                'tone': 'rose',
            },
            {
                'label': 'Pending Follow-Ups',
                'value': pending_followups,
                'trend': '-4.2%',
                'progress': 43,
                'icon': 'fa-phone-volume',
                'tone': 'blue',
            },
        ],
        'ai_insights': [
            f'{high_priority_count or 5} high-priority leads require follow-up',
            f'Expected revenue this month: ₹{round(revenue_forecast / 100000, 1)}L',
            'Enterprise lead conversion increased by 18%',
        ],
        'chart_data': {
            'pipeline': {
                'labels': [stage for stage, total in pipeline_stages],
                'values': [total for stage, total in pipeline_stages],
            },
            'revenue': {
                'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                'values': [2.1, 2.8, 3.4, 3.1, 4.2, 5.0],
            },
            'categories': {
                'labels': [name for name, total in category_counts],
                'values': [total or 1 for name, total in category_counts],
            },
            'conversion': {
                'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                'values': [18, 22, 25, 21, 31, 36],
            },
        },
        'kanban': kanban,
        'recommendations': [
            'Lead Acme Corp has 82% conversion probability.',
            'Schedule follow-up calls for all critical leads within 24 hours.',
            'Move proposal-stage opportunities into executive review this week.',
            'Review stalled SMB leads before month-end close.',
        ],
        'activities': [
            'AI generated a follow-up email for Acme Corp',
            'Lead status updated to Proposal',
            'High-value client detected in Enterprise pipeline',
            'Meeting scheduled with Northstar Finance',
            'Invoice draft generated for converted opportunity',
        ],
        'targets': [
            {'label': 'Revenue quota', 'value': '₹8L', 'progress': target_progress},
            {'label': 'Enterprise pipeline', 'value': '72%', 'progress': 72},
            {'label': 'Team response SLA', 'value': '91%', 'progress': 91},
            {'label': 'Follow-up completion', 'value': '68%', 'progress': 68},
        ],
    }


class DashboardView(RegularUserRequiredMixin, generic.View):
    template_name = 'dashboard/pages/dashboard_home.html'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setup(self, *args, **kwargs):
        return super().setup(*args, **kwargs)

    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        return render(request, self.template_name, build_dashboard_context())


class ForecastingView(RegularUserRequiredMixin, generic.View):
    template_name = 'dashboard/pages/forecasting.html'

    def get_context_data(self, ai_forecast=None):
        dataset = build_forecast_dataset()
        return {
            'local_forecast': build_local_forecast(dataset),
            'ai_forecast': ai_forecast,
        }

    def get(self, request):
        return render(
            request,
            self.template_name,
            self.get_context_data(),
        )

    def post(self, request):
        dataset = build_forecast_dataset()
        ai_forecast = get_gemini_forecast(dataset)
        return render(
            request,
            self.template_name,
            {
                'local_forecast': build_local_forecast(dataset),
                'ai_forecast': ai_forecast,
            },
        )
