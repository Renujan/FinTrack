from rest_framework import serializers
from transactions.models import DataImport


class DataImportFileUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=True, help_text="CSV file containing transaction data")
    create_missing_categories = serializers.BooleanField(
        default=False,
        required=False,
        help_text="If true, automatically creates missing categories during preview/execution"
    )

    def validate_file(self, value):
        if not value:
            raise serializers.ValidationError("CSV file is required.")
        filename = getattr(value, 'name', '')
        if not filename.lower().endswith('.csv'):
            raise serializers.ValidationError("File extension must be .csv")
        return value


class DataImportExecuteSerializer(serializers.Serializer):
    skip_duplicates = serializers.BooleanField(
        default=True,
        required=False,
        help_text="Skip duplicate transaction rows during import execution"
    )
    create_missing_categories = serializers.BooleanField(
        default=False,
        required=False,
        help_text="Automatically create unmatched categories during execution"
    )


class DataImportSerializer(serializers.ModelSerializer):
    user_email = serializers.ReadOnlyField(source='user.email')

    class Meta:
        model = DataImport
        fields = [
            'id',
            'user_email',
            'file_name',
            'status',
            'total_rows',
            'successful_rows',
            'failed_rows',
            'skipped_rows',
            'duplicate_rows',
            'error_summary',
            'preview_data',
            'created_at',
            'completed_at'
        ]
        read_only_fields = [
            'id', 'user_email', 'file_name', 'status', 'total_rows',
            'successful_rows', 'failed_rows', 'skipped_rows',
            'duplicate_rows', 'error_summary', 'preview_data',
            'created_at', 'completed_at'
        ]
