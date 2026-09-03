from rest_framework import serializers


class SummaryAnalyticsSerializer(serializers.Serializer):
    total_income = serializers.FloatField()
    total_expenses = serializers.FloatField()
    net_balance = serializers.FloatField()
    savings_rate = serializers.FloatField()
    transaction_count = serializers.IntegerField()
    income_transaction_count = serializers.IntegerField(required=False)
    expense_transaction_count = serializers.IntegerField(required=False)
    avg_income_transaction = serializers.FloatField(required=False)
    avg_expense_transaction = serializers.FloatField(required=False)


class IncomeExpenseAnalyticsSerializer(serializers.Serializer):
    income = serializers.FloatField()
    expenses = serializers.FloatField()
    net = serializers.FloatField()
    savings_rate = serializers.FloatField()
    transaction_count = serializers.IntegerField()
    income_count = serializers.IntegerField()
    expense_count = serializers.IntegerField()


class CategoryAnalyticsItemSerializer(serializers.Serializer):
    category = serializers.CharField()
    category_id = serializers.IntegerField(allow_null=True)
    amount = serializers.FloatField()
    spent = serializers.FloatField(required=False)
    percentage = serializers.FloatField()
    percentage_of_total = serializers.FloatField(required=False)
    transaction_count = serializers.IntegerField()


class IncomeCategoryAnalyticsItemSerializer(serializers.Serializer):
    category = serializers.CharField()
    category_id = serializers.IntegerField(allow_null=True)
    amount = serializers.FloatField()
    income = serializers.FloatField(required=False)
    percentage = serializers.FloatField()
    percentage_of_total = serializers.FloatField(required=False)
    transaction_count = serializers.IntegerField()


class DailyTrendItemSerializer(serializers.Serializer):
    date = serializers.CharField()
    income = serializers.FloatField()
    expenses = serializers.FloatField()
    net = serializers.FloatField()
    transaction_count = serializers.IntegerField()


class MonthlyTrendItemSerializer(serializers.Serializer):
    month = serializers.CharField()
    income = serializers.FloatField()
    expenses = serializers.FloatField()
    net = serializers.FloatField()
    net_balance = serializers.FloatField(required=False)
    transaction_count = serializers.IntegerField()
