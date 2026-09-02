from rest_framework import serializers
from django.urls import reverse
from transactions.models import DataExport
from transactions.choices import ExportType, ExportFormat, ExportStatus, TransactionType
from transactions.filters import validate_filter_params


class DataExportCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False, allow_blank=True, help_text="Optional custom export name")
    export_type = serializers.ChoiceField(
        choices=ExportType.choices,
        default=ExportType.FULL_FINANCIAL_DATA,
        help_text="Type of financial data to export"
    )
    format = serializers.ChoiceField(
        choices=ExportFormat.choices,
        default=ExportFormat.JSON,
        help_text="File format for export (CSV or JSON)"
    )
    start_date = serializers.DateField(required=False, allow_null=True, help_text="Filter start date (YYYY-MM-DD)")
    end_date = serializers.DateField(required=False, allow_null=True, help_text="Filter end date (YYYY-MM-DD)")
    category = serializers.IntegerField(required=False, allow_null=True, help_text="Filter category ID")
    transaction_type = serializers.ChoiceField(
        choices=TransactionType.choices,
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text="Filter transaction type (INCOME or EXPENSE)"
    )

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                'end_date': 'start_date must be less than or equal to end_date.'
            })

        return attrs


class DataExportListSerializer(serializers.ModelSerializer):
    is_expired = serializers.BooleanField(read_only=True)
    download_url = serializers.SerializerMethodNestedField if False else serializers.SerializerMethodField()

    class Meta:
        model = DataExport
        fields = [
            'id',
            'name',
            'export_type',
            'format',
            'status',
            'file_name',
            'file_size',
            'record_count',
            'filters',
            'created_at',
            'completed_at',
            'expires_at',
            'is_expired',
            'download_url',
        ]
        read_only_fields = fields

    def get_download_url(self, obj):
        request = self.context.get('request')
        if obj.status == ExportStatus.COMPLETED and obj.file and not obj.is_expired:
            url = reverse('transactions:export-download', kwargs={'pk': obj.pk})
            if request:
                return request.build_absolute_uri(url)
            return url
        return None


class DataExportDetailSerializer(DataExportListSerializer):
    class Meta(DataExportListSerializer.Meta):
        pass
