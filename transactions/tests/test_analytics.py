import datetime
from decimal import Decimal
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from transactions.choices import TransactionType, BudgetPeriod
from transactions.models import Category, Transaction, Budget

User = get_user_model()


@pytest.mark.django_db
class TestAnalyticsAPI:

    @pytest.fixture(autouse=True)
    def setup_data(self):
        self.client = APIClient()
        self.user_a = User.objects.create_user(
            username='user_a',
            email='usera@example.com',
            password='Password123!'
        )
        self.user_b = User.objects.create_user(
            username='user_b',
            email='userb@example.com',
            password='Password123!'
        )

        self.client.force_authenticate(user=self.user_a)

        self.cat_food = Category.objects.create(user=self.user_a, name='Food')
        self.cat_rent = Category.objects.create(user=self.user_a, name='Rent')
        self.cat_salary = Category.objects.create(user=self.user_a, name='Salary')

        self.t1 = Transaction.objects.create(
            user=self.user_a,
            category=self.cat_salary,
            transaction_type=TransactionType.INCOME,
            amount=Decimal('5000.00'),
            date=datetime.date(2026, 8, 1),
            description='Monthly Salary'
        )
        self.t2 = Transaction.objects.create(
            user=self.user_a,
            category=self.cat_rent,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('2000.00'),
            date=datetime.date(2026, 8, 2),
            description='August Rent'
        )
        self.t3 = Transaction.objects.create(
            user=self.user_a,
            category=self.cat_food,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('500.00'),
            date=datetime.date(2026, 8, 5),
            description='Groceries'
        )
        self.t4 = Transaction.objects.create(
            user=self.user_a,
            category=self.cat_food,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('300.00'),
            date=datetime.date(2026, 8, 10),
            description='Dining Out'
        )

    # 1. Summary Endpoint Tests
    def test_summary_unauthenticated_returns_401(self):
        self.client.logout()
        res = self.client.get('/api/analytics/summary/')
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_summary_success(self):
        res = self.client.get('/api/analytics/summary/')
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data['total_income'] == '5000.00'
        assert data['total_expenses'] == '2800.00'
        assert data['net_balance'] == '2200.00'
        assert data['transaction_count'] == 4
        assert data['income_transaction_count'] == 1
        assert data['expense_transaction_count'] == 3
        assert data['avg_income_transaction'] == '5000.00'
        assert data['avg_expense_transaction'] == '933.33'

    def test_summary_user_isolation(self):
        self.client.force_authenticate(user=self.user_b)
        res = self.client.get('/api/analytics/summary/')
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data['total_income'] == '0.00'
        assert data['total_expenses'] == '0.00'
        assert data['net_balance'] == '0.00'
        assert data['transaction_count'] == 0

    def test_summary_date_filtering(self):
        res = self.client.get('/api/analytics/summary/?start_date=2026-08-02&end_date=2026-08-06')
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data['total_income'] == '0.00'
        assert data['total_expenses'] == '2500.00'
        assert data['net_balance'] == '-2500.00'
        assert data['transaction_count'] == 2

    def test_summary_invalid_date_returns_400(self):
        res = self.client.get('/api/analytics/summary/?start_date=invalid-date')
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert 'start_date' in res.json()

    def test_summary_start_date_after_end_date_returns_400(self):
        res = self.client.get('/api/analytics/summary/?start_date=2026-08-31&end_date=2026-08-01')
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert 'start_date' in res.json()

    # 2. Financial Trends Endpoint Tests
    def test_trends_unauthenticated_returns_401(self):
        self.client.logout()
        res = self.client.get('/api/analytics/trends/')
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_trends_monthly_grouping(self):
        res = self.client.get('/api/analytics/trends/?group_by=monthly')
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert len(data) == 1
        assert data[0]['period'] == '2026-08'
        assert data[0]['income'] == '5000.00'
        assert data[0]['expenses'] == '2800.00'
        assert data[0]['net'] == '2200.00'
        assert data[0]['transaction_count'] == 4

    def test_trends_daily_grouping(self):
        res = self.client.get('/api/analytics/trends/?group_by=daily')
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert len(data) == 4
        assert data[0]['period'] == '2026-08-01'
        assert data[0]['income'] == '5000.00'

    def test_trends_weekly_grouping(self):
        res = self.client.get('/api/analytics/trends/?group_by=weekly')
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert len(data) >= 1

    def test_trends_invalid_grouping_returns_400(self):
        res = self.client.get('/api/analytics/trends/?group_by=hourly')
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert 'group_by' in res.json()

    # 3. Monthly Summary Endpoint Tests
    def test_monthly_summary_unauthenticated_returns_401(self):
        self.client.logout()
        res = self.client.get('/api/analytics/monthly/')
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_monthly_summary_success(self):
        # Create transaction in July 2026
        Transaction.objects.create(
            user=self.user_a,
            category=self.cat_salary,
            transaction_type=TransactionType.INCOME,
            amount=Decimal('4000.00'),
            date=datetime.date(2026, 7, 15),
            description='July Salary'
        )

        res = self.client.get('/api/analytics/monthly/')
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert len(data) == 2
        assert data[0]['month'] == '2026-07'
        assert data[0]['income'] == '4000.00'
        assert data[1]['month'] == '2026-08'
        assert data[1]['income'] == '5000.00'

    # 4. Category Spending Analytics & Top Spending Categories
    def test_category_analytics_unauthenticated_returns_401(self):
        self.client.logout()
        res = self.client.get('/api/analytics/categories/')
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_category_analytics_expense_breakdown(self):
        res = self.client.get('/api/analytics/categories/')
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert len(data) == 2  # Rent and Food (Salary is income)
        # Rent: 2000 / 2800 = 71.43%
        assert data[0]['category'] == 'Rent'
        assert data[0]['spent'] == '2000.00'
        assert data[0]['percentage_of_total'] == 71.43
        # Food: 800 / 2800 = 28.57%
        assert data[1]['category'] == 'Food'
        assert data[1]['spent'] == '800.00'
        assert data[1]['percentage_of_total'] == 28.57

    def test_category_analytics_top_spending_limit(self):
        res = self.client.get('/api/analytics/categories/?limit=1')
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert len(data) == 1
        assert data[0]['category'] == 'Rent'

    def test_category_analytics_invalid_limit_returns_400(self):
        res = self.client.get('/api/analytics/categories/?limit=invalid')
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert 'limit' in res.json()

        res2 = self.client.get('/api/analytics/categories/?limit=-5')
        assert res2.status_code == status.HTTP_400_BAD_REQUEST

    # 5. Period Comparison Tests
    def test_comparison_unauthenticated_returns_401(self):
        self.client.logout()
        res = self.client.get('/api/analytics/comparison/')
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_comparison_success_with_dates(self):
        # Create previous period transactions (July 1 - July 31)
        Transaction.objects.create(
            user=self.user_a,
            category=self.cat_salary,
            transaction_type=TransactionType.INCOME,
            amount=Decimal('4000.00'),
            date=datetime.date(2026, 7, 10)
        )
        Transaction.objects.create(
            user=self.user_a,
            category=self.cat_rent,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('2000.00'),
            date=datetime.date(2026, 7, 12)
        )

        res = self.client.get('/api/analytics/comparison/?start_date=2026-08-01&end_date=2026-08-31')
        assert res.status_code == status.HTTP_200_OK
        data = res.json()

        assert data['current_period']['income'] == '5000.00'
        assert data['current_period']['expenses'] == '2800.00'
        assert data['previous_period']['income'] == '4000.00'
        assert data['previous_period']['expenses'] == '2000.00'
        # income change: (5000 - 4000) / 4000 * 100 = 25.00%
        assert data['income_change'] == '25.00'
        # expense change: (2800 - 2000) / 2000 * 100 = 40.00%
        assert data['expense_change'] == '40.00'

    def test_comparison_zero_previous_value_safety(self):
        # Period where previous income was 0
        res = self.client.get('/api/analytics/comparison/?start_date=2026-08-01&end_date=2026-08-31')
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert 'income_change' in data
        assert 'expense_change' in data

    # 6. Budget Analytics Integration Tests
    def test_budget_analytics_unauthenticated_returns_401(self):
        self.client.logout()
        res = self.client.get('/api/analytics/budgets/')
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_budget_analytics_success(self):
        # Create budgets for user_a
        Budget.objects.create(
            user=self.user_a,
            category=self.cat_food,
            name='Food Budget',
            amount=Decimal('500.00'),
            period=BudgetPeriod.MONTHLY,
            start_date=datetime.date(2026, 8, 1),
            end_date=datetime.date(2026, 8, 31)
        )
        Budget.objects.create(
            user=self.user_a,
            category=None,
            name='Overall Budget',
            amount=Decimal('5000.00'),
            period=BudgetPeriod.MONTHLY,
            start_date=datetime.date(2026, 8, 1),
            end_date=datetime.date(2026, 8, 31)
        )

        res = self.client.get('/api/analytics/budgets/')
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data['total_budgets'] == 2
        # Food spending is 800.00, budget is 500.00 -> exceeded!
        assert data['exceeded_budgets_count'] == 1
        assert data['total_budgeted_amount'] == '5500.00'
        # Total spent: 800 (Food) + 2800 (Overall) = 3600
        assert data['total_budget_spending'] == '3600.00'
        assert len(data['budgets_summary']) == 2

    def test_budget_analytics_user_isolation(self):
        Budget.objects.create(
            user=self.user_a,
            category=self.cat_food,
            name='Food Budget',
            amount=Decimal('500.00'),
            period=BudgetPeriod.MONTHLY,
            start_date=datetime.date(2026, 8, 1),
            end_date=datetime.date(2026, 8, 31)
        )

        self.client.force_authenticate(user=self.user_b)
        res = self.client.get('/api/analytics/budgets/')
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data['total_budgets'] == 0
        assert len(data['budgets_summary']) == 0

    # 7. User Data Isolation and Query Override Protection
    def test_query_param_user_override_ignored(self):
        res = self.client.get(f'/api/analytics/summary/?user_id={self.user_b.id}')
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        # Returns user_a data, NOT user_b data
        assert data['total_income'] == '5000.00'
