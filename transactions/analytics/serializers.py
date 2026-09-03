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


class BudgetSummaryItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    category_name = serializers.CharField(allow_null=True)
    is_overall = serializers.BooleanField()
    budget_amount = serializers.FloatField()
    spent_amount = serializers.FloatField()
    remaining_amount = serializers.FloatField()
    percentage_used = serializers.FloatField()
    is_exceeded = serializers.BooleanField()


class BudgetAnalyticsSerializer(serializers.Serializer):
    total_budgets = serializers.IntegerField()
    active_budgets_count = serializers.IntegerField()
    exceeded_budgets_count = serializers.IntegerField()
    total_budgeted_amount = serializers.FloatField()
    total_budget_spending = serializers.FloatField()
    overall_budget_utilization = serializers.FloatField()
    budgets_summary = serializers.ListField(child=BudgetSummaryItemSerializer())


class RecentTransactionAnalyticsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    amount = serializers.FloatField()
    transaction_type = serializers.CharField()
    date = serializers.CharField()
    category_id = serializers.IntegerField(allow_null=True)
    category_name = serializers.CharField(allow_null=True)
