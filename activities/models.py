from django.db import models


class Activity(models.Model):
    CALL = 'call'
    EMAIL = 'email'
    MEETING = 'meeting'
    NOTE = 'note'
    TASK = 'task'

    ACTIVITY_TYPES = [
        (CALL, 'Call'),
        (EMAIL, 'Email'),
        (MEETING, 'Meeting'),
        (NOTE, 'Note'),
        (TASK, 'Task'),
    ]

    lead = models.ForeignKey(
        'leads.Lead',
        related_name='activities',
        on_delete=models.CASCADE,
    )
    activity_type = models.CharField(
        max_length=20,
        choices=ACTIVITY_TYPES,
        default=NOTE,
    )
    title = models.CharField(max_length=120)
    notes = models.TextField(blank=True)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'activities'

    def __str__(self):
        return self.title
