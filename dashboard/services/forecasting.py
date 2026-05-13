import json
import urllib.error
import urllib.request
from decimal import Decimal

from django.conf import settings
from django.db.models import Count, Sum
from django.utils import timezone

from activities.models import Activity
from leads.models import Lead


FORECAST_STATUS_WEIGHTS = {
    Lead.STATUS_NEW: Decimal('0.10'),
    Lead.STATUS_CONTACTED: Decimal('0.25'),
    Lead.STATUS_FOLLOW_UP: Decimal('0.40'),
    Lead.STATUS_NEGOTIATION: Decimal('0.70'),
    Lead.STATUS_LOST: Decimal('0.00'),
    Lead.STATUS_CONVERTED: Decimal('1.00'),
}


def _money(value):
    return Decimal(value or 0)


def _format_money(value):
    return f'Rs. {_money(value):,.2f}'


def _chart_value(value):
    return float(_money(value))


def _lead_payload(lead):
    return {
        'id': lead.id,
        'status': lead.status,
        'revenue': str(lead.revenue),
        'category': lead.category.name if lead.category else '',
        'agent': str(lead.agent) if lead.agent else '',
        'age': lead.age,
        'created_at': lead.created_at.isoformat() if lead.created_at else '',
        'updated_at': lead.updated_at.isoformat() if lead.updated_at else '',
        'activities': [
            {
                'activity_type': activity.activity_type,
                'completed': activity.completed,
                'created_at': (
                    activity.created_at.isoformat()
                    if activity.created_at else ''
                ),
                'updated_at': (
                    activity.updated_at.isoformat()
                    if activity.updated_at else ''
                ),
            }
            for activity in lead.activities.all()[:8]
        ],
    }


def build_forecast_dataset(limit=40):
    leads = list(
        Lead.objects.select_related('category', 'agent')
        .prefetch_related('activities')
        .order_by('-updated_at', '-id')[:limit]
    )

    pipeline_value = sum(
        _money(lead.revenue)
        for lead in leads
        if lead.status not in [Lead.STATUS_LOST, Lead.STATUS_CONVERTED]
    )
    weighted_value = sum(
        _money(lead.revenue)
        * FORECAST_STATUS_WEIGHTS.get(lead.status, Decimal('0.10'))
        for lead in leads
    )
    converted_value = sum(
        _money(lead.revenue)
        for lead in leads
        if lead.status == Lead.STATUS_CONVERTED
    )
    lost_deals = Lead.objects.filter(status=Lead.STATUS_LOST).aggregate(
        total=Count('id'),
    )
    lost_count = lost_deals['total'] or 0
    growth_chart = {
        'labels': ['Completed', 'Forecast', 'Open Pipeline'],
        'values': [
            _chart_value(converted_value),
            _chart_value(weighted_value),
            _chart_value(pipeline_value),
        ],
    }

    status_counts = list(
        Lead.objects.values('status')
        .annotate(total=Count('id'), revenue=Sum('revenue'))
        .order_by('status')
    )
    category_counts = list(
        Lead.objects.values('category__name')
        .annotate(total=Count('id'), revenue=Sum('revenue'))
        .order_by('-total')[:8]
    )
    agent_counts = list(
        Lead.objects.values('agent__first_name', 'agent__last_name')
        .annotate(total=Count('id'), revenue=Sum('revenue'))
        .order_by('-total')[:8]
    )
    activity_counts = list(
        Activity.objects.values('activity_type', 'completed')
        .annotate(total=Count('id'))
        .order_by('activity_type', 'completed')
    )

    return {
        'generated_at': timezone.now().isoformat(),
        'lead_count': Lead.objects.count(),
        'activity_count': Activity.objects.count(),
        'pipeline_value': str(pipeline_value),
        'weighted_forecast_value': str(weighted_value),
        'converted_value': str(converted_value),
        'lost_count': lost_count,
        'growth_chart': growth_chart,
        'status_counts': status_counts,
        'category_counts': category_counts,
        'agent_counts': agent_counts,
        'activity_counts': activity_counts,
        'leads': [_lead_payload(lead) for lead in leads],
    }


def build_local_forecast(dataset):
    return {
        'pipeline_value': _format_money(dataset['pipeline_value']),
        'weighted_forecast_value': _format_money(
            dataset['weighted_forecast_value']
        ),
        'converted_value': _format_money(dataset['converted_value']),
        'lost_count': dataset['lost_count'],
        'growth_chart': dataset['growth_chart'],
        'lead_count': dataset['lead_count'],
        'activity_count': dataset['activity_count'],
        'status_counts': dataset['status_counts'],
        'category_counts': dataset['category_counts'],
        'agent_counts': dataset['agent_counts'],
        'activity_counts': dataset['activity_counts'],
    }


def _extract_gemini_text(response_data):
    parts = []
    for candidate in response_data.get('candidates', []):
        content = candidate.get('content', {})
        for part in content.get('parts', []):
            text = part.get('text')
            if text:
                parts.append(text)

    return '\n'.join(parts).strip()


def _build_prompt(dataset):
    return (
        'You are forecasting sales for a small single-user CRM. '
        'Use only the provided lead and activity data. '
        'The agent field means the outside person/source bringing orders, '
        'not the internal CRM owner. '
        'Give a concise forecast with: expected sales amount, likely sales '
        'count, lost-deal impact, top risks, top opportunities, and '
        'immediate actions. '
        'Use the growth_chart values to align your text forecast with the '
        'graph shown in the UI. '
        'Do not invent close dates, lead sources, owners, lost reasons, or '
        'probability fields.\n\n'
        f'CRM data JSON:\n{json.dumps(dataset, default=str)}'
    )


def get_gemini_forecast(dataset):
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if not api_key:
        return {
            'ok': False,
            'message': (
                'Gemini API key is not configured. Add it in '
                'config/gemini_config.py.'
            ),
        }

    body = {
        'contents': [
            {
                'role': 'user',
                'parts': [
                    {'text': _build_prompt(dataset)},
                ],
            },
        ],
        'generationConfig': {
            'maxOutputTokens': 900,
            'temperature': 0.2,
        },
    }
    url = (
        f'{settings.GEMINI_API_BASE_URL}/'
        f'{settings.GEMINI_MODEL}:generateContent'
    )
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode('utf-8'),
        headers={
            'x-goog-api-key': api_key,
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=settings.GEMINI_TIMEOUT_SECONDS,
        ) as response:
            response_data = json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as error:
        details = error.read().decode('utf-8', errors='replace')
        return {
            'ok': False,
            'message': f'Gemini request failed: {error.code} {details}',
        }
    except urllib.error.URLError as error:
        return {
            'ok': False,
            'message': f'Gemini request failed: {error.reason}',
        }
    except TimeoutError:
        return {
            'ok': False,
            'message': 'Gemini request timed out. Try again shortly.',
        }

    forecast_text = _extract_gemini_text(response_data)
    return {
        'ok': bool(forecast_text),
        'message': forecast_text or 'Gemini returned an empty forecast.',
    }
