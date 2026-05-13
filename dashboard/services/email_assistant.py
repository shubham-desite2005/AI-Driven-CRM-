import json
import urllib.error
import urllib.request

from django.conf import settings
from django.core.mail import BadHeaderError, send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


def _extract_gemini_text(response_data):
    parts = []
    for candidate in response_data.get('candidates', []):
        content = candidate.get('content', {})
        for part in content.get('parts', []):
            text = part.get('text')
            if text:
                parts.append(text)

    return '\n'.join(parts).strip()


def _lead_context(lead):
    if not lead:
        return {
            'name': '',
            'email': '',
            'category': '',
            'status': '',
            'revenue': '',
            'agent': '',
        }

    return {
        'name': f'{lead.first_name} {lead.last_name}'.strip(),
        'email': lead.email,
        'category': lead.category.name if lead.category else '',
        'status': lead.status,
        'revenue': str(lead.revenue),
        'agent': str(lead.agent) if lead.agent else '',
    }


def _build_prompt(action, lead, recipient, condition, email_body):
    lead_data = _lead_context(lead)
    condition_text = condition or 'Write a polite sales follow-up.'

    if action == 'fix_grammar':
        return (
            'You are an email editor inside a CRM. Fix grammar, spelling, '
            'punctuation, and clarity in the draft below while preserving the '
            'sender intent, meaning, and any specific offer or condition. '
            'Return only the improved email with a Subject line if one is '
            'already present or helpful. Do not add markdown.\n\n'
            f'Recipient: {recipient}\n'
            f'Lead context JSON: {json.dumps(lead_data, default=str)}\n'
            f'Condition or goal: {condition_text}\n\n'
            f'Draft email:\n{email_body}'
        )

    return (
        'You are an AI email assistant inside a CRM. Write a professional, '
        'specific follow-up email for the recipient using only the provided '
        'lead context and condition. Keep it concise, human, and actionable. '
        'Return only the finished email in this format: Subject: ... followed '
        'by the body. Do not add markdown or placeholders.\n\n'
        f'Recipient: {recipient}\n'
        f'Lead context JSON: {json.dumps(lead_data, default=str)}\n'
        f'Condition or goal: {condition_text}'
    )


def _local_followup(lead, condition):
    lead_data = _lead_context(lead)
    name = lead_data['name'] or 'there'
    category = lead_data['category'] or 'your current priorities'
    goal = condition or 'align on the next steps'

    return (
        f'Subject: Next steps for {name}\n\n'
        f'Hi {name},\n\n'
        f'I wanted to follow up based on your {category} requirements. '
        f'{goal[0].upper() + goal[1:] if goal else goal}\n\n'
        'Would you be open to a short call this week so we can confirm the '
        'timeline, success criteria, and best next action?\n\n'
        'Best regards,\n'
        'SalesOps Team'
    )


def parse_email_draft(email_body):
    lines = email_body.strip().splitlines()
    subject = 'Follow-up'
    body_lines = []

    for line in lines:
        if line.lower().startswith('subject:') and subject == 'Follow-up':
            subject = line.split(':', 1)[1].strip() or subject
        else:
            body_lines.append(line)

    return subject, '\n'.join(body_lines).strip()


def send_email_message(recipient, email_body):
    recipient = (recipient or '').strip()
    email_body = (email_body or '').strip()

    try:
        validate_email(recipient)
    except ValidationError:
        return {
            'ok': False,
            'message': 'Enter a valid recipient email address.',
        }

    if not email_body:
        return {
            'ok': False,
            'message': 'Write or generate an email before sending.',
        }

    subject, body = parse_email_draft(email_body)
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', '') or getattr(
        settings,
        'EMAIL_HOST_USER',
        '',
    )

    if not from_email:
        return {
            'ok': False,
            'message': 'Sender email is not configured.',
        }

    try:
        sent_count = send_mail(
            subject,
            body,
            from_email,
            [recipient],
            fail_silently=False,
        )
    except BadHeaderError:
        return {
            'ok': False,
            'message': 'Invalid email header detected.',
        }
    except Exception as error:
        return {
            'ok': False,
            'message': f'Email sending failed: {error}',
        }

    return {
        'ok': sent_count == 1,
        'message': (
            f'Email sent to {recipient}.'
            if sent_count == 1
            else 'Email could not be sent.'
        ),
    }


def get_gemini_email(action, lead=None, recipient='', condition='', email_body=''):
    if action == 'generate' and not getattr(settings, 'GEMINI_API_KEY', ''):
        return {
            'ok': True,
            'message': _local_followup(lead, condition),
            'source': 'local',
        }

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
                    {
                        'text': _build_prompt(
                            action,
                            lead,
                            recipient,
                            condition,
                            email_body,
                        ),
                    },
                ],
            },
        ],
        'generationConfig': {
            'maxOutputTokens': 900,
            'temperature': 0.25 if action == 'generate' else 0.1,
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

    email_text = _extract_gemini_text(response_data)
    return {
        'ok': bool(email_text),
        'message': email_text or 'Gemini returned an empty email draft.',
        'source': 'gemini',
    }
