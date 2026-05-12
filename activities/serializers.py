from rest_framework import serializers

from .models import Activity


class ActivitySerializer(serializers.ModelSerializer):
    lead_name = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = [
            'id',
            'lead',
            'lead_name',
            'activity_type',
            'title',
            'notes',
            'completed',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_lead_name(self, obj):
        return str(obj.lead)
