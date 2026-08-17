from rest_framework import serializers


class SummaryAnalyticsSerializer(serializers.Serializer):
    total_income = serializers.CharField()
    total_expenses = serializers.CharField()
    net_balance = serializers.CharField()
    transaction_count = serializers.IntegerField()
    income_transaction_count = serializers.IntegerField()
    expense_transaction_count = serializers.IntegerField()
    avg_income_transaction = serializers.CharField()
    avg_expense_transaction = serializers.CharField()


class TrendItemSerializer(serializers.Serializer):
    period = serializers.CharField()
    income = serializers.CharField()
    expenses = serializers.CharField()
    net = serializers.CharField()
    transaction_count = serializers.IntegerField()


class MonthlySummaryItemSerializer(serializers.Serializer):
    month = serializers.CharField()
    income = serializers.CharField()
    expenses = serializers.CharField()
    net_balance = serializers.CharField()
    transaction_count = serializers.IntegerField()


class CategoryAnalyticsItemSerializer(serializers.Serializer):
    category = serializers.CharField()
    category_id = serializers.IntegerField(allow_null=True)
    spent = serializers.CharField()
    transaction_count = serializers.IntegerField()
    percentage_of_total = serializers.FloatField()


class PeriodMetricSerializer(serializers.Serializer):
    start_date = serializers.CharField()
    end_date = serializers.CharField()
    income = serializers.CharField()
    expenses = serializers.CharField()
    net_balance = serializers.CharField()
    transaction_count = serializers.IntegerField()


class PeriodComparisonSerializer(serializers.Serializer):
    current_period = PeriodMetricSerializer()
    previous_period = PeriodMetricSerializer()
    income_change = serializers.CharField()
    expense_change = serializers.CharField()
    net_change = serializers.CharField()


class BudgetSummaryItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    category_name = serializers.CharField(allow_null=True)
    is_overall = serializers.BooleanField()
    budget_amount = serializers.CharField()
    spent_amount = serializers.CharField()
    remaining_amount = serializers.CharField()
    percentage_used = serializers.FloatField()
    is_exceeded = serializers.BooleanField()


class BudgetAnalyticsSerializer(serializers.Serializer):
    total_budgets = serializers.IntegerField()
    active_budgets_count = serializers.IntegerField()
    exceeded_budgets_count = serializers.IntegerField()
    total_budgeted_amount = serializers.CharField()
    total_budget_spending = serializers.CharField()
    overall_budget_utilization = serializers.FloatField()
    budgets_summary = serializers.ListField(child=BudgetSummaryItemSerializer())
