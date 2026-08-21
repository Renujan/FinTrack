import datetime
from rest_framework import serializers


class ReportDateRangeSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False, format='%Y-%m-%d', input_formats=['%Y-%m-%d'])
    end_date = serializers.DateField(required=False, format='%Y-%m-%d', input_formats=['%Y-%m-%d'])

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                'start_date': ["start_date cannot be greater than end_date."]
            })
        return attrs


class TransactionImportFileUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)

    def validate_file(self, file_obj):
        if not file_obj:
            raise serializers.ValidationError("No file was uploaded.")

        # Check file extension
        if not file_obj.name.lower().endswith('.csv'):
            raise serializers.ValidationError("Only CSV files are supported.")

        # Check file size (5MB limit)
        max_size = 5 * 1024 * 1024
        if file_obj.size > max_size:
            raise serializers.ValidationError("File size exceeds 5MB limit.")

        if file_obj.size == 0:
            raise serializers.ValidationError("Uploaded file is empty.")

        return file_obj
