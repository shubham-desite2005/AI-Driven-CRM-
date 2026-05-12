from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Agent(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.CharField(max_length=30)
    phone_number = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Lead(models.Model):
    STATUS_NEW = '🟢 New Lead'
    STATUS_CONTACTED = '🔵 Contacted'
    STATUS_FOLLOW_UP = '🟡 Follow-Up'
    STATUS_NEGOTIATION = '🟣 Negotiation'
    STATUS_LOST = '🔴 Lost'
    STATUS_CONVERTED = '✅ Converted'

    STATUS_CHOICES = [
        (STATUS_NEW, STATUS_NEW),
        (STATUS_CONTACTED, STATUS_CONTACTED),
        (STATUS_FOLLOW_UP, STATUS_FOLLOW_UP),
        (STATUS_NEGOTIATION, STATUS_NEGOTIATION),
        (STATUS_LOST, STATUS_LOST),
        (STATUS_CONVERTED, STATUS_CONVERTED),
    ]

    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(max_length=30)
    age = models.IntegerField(default=0)
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
    )
    revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0'))],
    )
    category = models.ForeignKey(
        "Category", null=True, on_delete=models.SET_NULL)
    agent = models.ForeignKey("Agent", null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def masked_email(self):
        email = self.email or ''

        if '@' not in email:
            return f'{email[:3]}***'

        username, domain = email.split('@', 1)
        return f'{username[:3]}***@{domain}'
