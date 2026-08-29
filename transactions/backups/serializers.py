from rest_framework import serializers
from django.urls import reverse
from transactions.models import DataBackup
from transactions.choices import BackupStatus, BackupType


class DataBackupSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = DataBackup
        fields = [
            'id',
            'name',
            'status',
            'backup_type',
            'file_size',
            'record_count',
            'metadata',
            'created_at',
            'completed_at',
            'expires_at',
            'is_expired',
            'download_url',
        ]
        read_only_fields = [
            'id',
            'status',
            'file_size',
            'record_count',
            'metadata',
            'created_at',
            'completed_at',
            'expires_at',
            'is_expired',
            'download_url',
        ]

    def get_download_url(self, obj):
        if obj.status != BackupStatus.COMPLETED or not obj.file:
            return None
        request = self.context.get('request')
        relative_url = reverse('transactions:backup-download', kwargs={'pk': obj.pk})
        if request:
            return request.build_absolute_uri(relative_url)
        return relative_url


class DataBackupCreateSerializer(serializers.Serializer):
    name = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Optional custom name for the backup record"
    )
    backup_type = serializers.ChoiceField(
        choices=BackupType.choices,
        default=BackupType.FULL,
        help_text="Backup type: FULL, TRANSACTIONS, or SELECTED_DATA"
    )
    include_sections = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        default=list,
        help_text="Specific sections to include for SELECTED_DATA (e.g. ['transactions', 'budgets', 'goals', 'categories', 'recurring'])"
    )
    retention_days = serializers.IntegerField(
        required=False,
        default=30,
        min_value=1,
        max_value=365,
        help_text="Number of days before backup expires (1-365 days, default 30)"
    )


class RestoreValidationRequestSerializer(serializers.Serializer):
    file = serializers.FileField(
        required=False,
        help_text="Uploaded JSON backup file to validate"
    )
    json_data = serializers.JSONField(
        required=False,
        help_text="Raw JSON backup payload to validate"
    )

    def validate(self, data):
        if not data.get('file') and data.get('json_data') is None:
            raise serializers.ValidationError("Either 'file' upload or 'json_data' payload must be provided for restore validation.")
        return data
