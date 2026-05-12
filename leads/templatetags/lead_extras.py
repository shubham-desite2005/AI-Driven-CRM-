from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def currency(value, symbol='₹'):
    try:
        amount = Decimal(value or 0)
    except (InvalidOperation, TypeError, ValueError):
        amount = Decimal('0')

    return f'{symbol}{amount:,.2f}'
