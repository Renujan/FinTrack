from rest_framework import serializers


class DashboardFinancialSummarySerializer(serializers.Serializer):
    total_income = serializers.CharField()
    total_expenses = serializers.CharField()
    current_balance = serializers.CharField()
    net_cash_flow = serializers.CharField()


class PeriodDetailSerializer(serializers.Serializer):
    start_date = serializers.CharField()
    end_date = serializers.CharField()
    income = serializers.CharField()
    expenses = serializers.CharField()


class IncomeExpenseOverviewSerializer(serializers.Serializer):
    period_type = serializers.CharField()
    current_period = PeriodDetailSerializer()
    previous_period = PeriodDetailSerializer()
    income_percentage_change = serializers.CharField()
    expense_percentage_change = serializers.CharField()


class BalanceSummarySerializer(serializers.Serializer):
    total_income = serializers.CharField()
    total_expenses = serializers.CharField()
    current_balance = serializers.CharField()
    transaction_count = serializers.IntegerField()
    income_transaction_count = serializers.IntegerField()
    expense_transaction_count = serializers.IntegerField()
    balance_type = serializers.CharField()
    note = serializers.CharField()


class CashFlowSummaryItemSerializer(serializers.Serializer):
    period = serializers.CharField()
    income = serializers.CharField()
    expenses = serializers.CharField()
    net_cash_flow = serializers.CharField()
    transaction_count = serializers.IntegerField()


class CategoryMinSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class RecentTransactionItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    amount = serializers.CharField()
    transaction_type = serializers.CharField()
    category = CategoryMinSerializer(allow_null=True)
    category_name = serializers.CharField()
    date = serializers.CharField()


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
    is_near_limit = serializers.BooleanField()


class BudgetOverviewSerializer(serializers.Serializer):
    total_budgets = serializers.IntegerField()
    active_budgets = serializers.IntegerField()
    exceeded_budgets = serializers.IntegerField()
    budgets_near_limit = serializers.IntegerField()
    total_budget_amount = serializers.CharField()
    total_spent_amount = serializers.CharField()
    remaining_amount = serializers.CharField()
    overall_utilization_percentage = serializers.FloatField()
    budgets_summary = BudgetSummaryItemSerializer(many=True)


class GoalSummaryItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    category_name = serializers.CharField(allow_null=True)
    target_amount = serializers.CharField()
    current_amount = serializers.CharField()
    remaining_amount = serializers.CharField()
    percentage_complete = serializers.FloatField()
    status = serializers.CharField()
    is_completed = serializers.BooleanField()
    is_near_completion = serializers.BooleanField()
    target_date = serializers.CharField()
    days_remaining = serializers.IntegerField()


class GoalOverviewSerializer(serializers.Serializer):
    total_goals = serializers.IntegerField()
    active_goals = serializers.IntegerField()
    completed_goals = serializers.IntegerField()
    near_completion_goals = serializers.IntegerField()
    total_target_amount = serializers.CharField()
    total_saved_amount = serializers.CharField()
    overall_progress_percentage = serializers.FloatField()
    goals_summary = GoalSummaryItemSerializer(many=True)


class TopCategoryItemSerializer(serializers.Serializer):
    category = serializers.CharField()
    category_id = serializers.IntegerField(allow_null=True)
    spent = serializers.CharField()
    percentage = serializers.FloatField()
    transaction_count = serializers.IntegerField()


class LargestExpenseItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    amount = serializers.CharField()
    category_name = serializers.CharField()
    date = serializers.CharField()


class SpendingInsightsSerializer(serializers.Serializer):
    highest_spending_category = TopCategoryItemSerializer(allow_null=True)
    largest_recent_expense = LargestExpenseItemSerializer(allow_null=True)
    average_expense = serializers.CharField()
    spending_change_percentage = serializers.CharField()
    expense_transaction_count = serializers.IntegerField()
    total_expenses_amount = serializers.CharField()


class MonthlyComparisonSerializer(serializers.Serializer):
    current_month = serializers.CharField()
    previous_month = serializers.CharField()
    current_income = serializers.CharField()
    previous_income = serializers.CharField()
    income_difference = serializers.CharField()
    income_percentage_change = serializers.CharField()
    current_expenses = serializers.CharField()
    previous_expenses = serializers.CharField()
    expense_difference = serializers.CharField()
    expense_percentage_change = serializers.CharField()
    current_balance = serializers.CharField()
    previous_balance = serializers.CharField()
    balance_difference = serializers.CharField()
    balance_percentage_change = serializers.CharField()


class DashboardAlertItemSerializer(serializers.Serializer):
    type = serializers.CharField()
    message = serializers.CharField()
    severity = serializers.CharField()
    category = serializers.CharField()
    metadata = serializers.DictField(required=False)


class FinancialDashboardResponseSerializer(serializers.Serializer):
    financial_summary = DashboardFinancialSummarySerializer()
    income_expense_overview = IncomeExpenseOverviewSerializer()
    balance_summary = BalanceSummarySerializer()
    cash_flow_summary = CashFlowSummaryItemSerializer(many=True)
    recent_transactions = RecentTransactionItemSerializer(many=True)
    budget_overview = BudgetOverviewSerializer()
    goal_overview = GoalOverviewSerializer()
    spending_insights = SpendingInsightsSerializer()
    top_categories = TopCategoryItemSerializer(many=True)
    monthly_comparison = MonthlyComparisonSerializer()
    alerts = DashboardAlertItemSerializer(many=True)
