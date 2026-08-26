from rest_framework import serializers


class ReportQueryFilterSerializer(serializers.Serializer):
    """
    Serializer for parsing and validating financial report query parameters.
    Ensures start_date <= end_date and validates date formats (YYYY-MM-DD).
    """
    start_date = serializers.DateField(required=False, input_formats=['%Y-%m-%d'])
    end_date = serializers.DateField(required=False, input_formats=['%Y-%m-%d'])
    category = serializers.CharField(required=False, allow_blank=True, help_text="Category ID or name filter")
    search = serializers.CharField(required=False, allow_blank=True, help_text="Search text filter")
    period = serializers.CharField(required=False, allow_blank=True, default='monthly', help_text="Trend period: daily, weekly, monthly")
    group_by = serializers.CharField(required=False, allow_blank=True, help_text="Alias for period grouping")
    limit = serializers.IntegerField(required=False, default=5, min_value=1, max_value=100, help_text="Limit for top categories report")

    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                'start_date': ["start_date cannot be greater than end_date."]
            })
        return data
