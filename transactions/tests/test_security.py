import io
import pytest
from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from django.core.management import call_command
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User
from transactions.models import Category, Transaction, Budget, FinancialGoal, RecurringTransaction, Notification, AuditLog
from transactions.choices import TransactionType, BudgetPeriod, RecurrenceFrequency


@pytest.fixture
def user(db):
    return User.objects.create_user(username='sec_user', email='sec@test.com', password='password123')


@pytest.mark.django_db
class TestAuthenticationSecurity:
    def test_missing_authentication_token_returns_401(self):
        client = APIClient()
        url = reverse('transactions:transaction-list-create')
        response = client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_authentication_token_returns_401(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token_string_xyz')
        url = reverse('transactions:transaction-list-create')
        response = client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token_rotation_and_blacklisting(self, user):
        refresh = RefreshToken.for_user(user)
        refresh_str = str(refresh)

        client = APIClient()
        url = reverse('authentication:token_refresh')
        res = client.post(url, {'refresh': refresh_str})

        assert res.status_code == status.HTTP_200_OK
        assert 'access' in res.data
        assert 'refresh' in res.data

        res_reuse = client.post(url, {'refresh': refresh_str})
        assert res_reuse.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestPermissionAndIDORIsolation:
    @pytest.fixture
    def user1(self):
        return User.objects.create_user(username='user1', email='u1@test.com', password='password123')

    @pytest.fixture
    def user2(self):
        return User.objects.create_user(username='user2', email='u2@test.com', password='password123')

    @pytest.fixture
    def client1(self, user1):
        c = APIClient()
        c.force_authenticate(user=user1)
        return c

    @pytest.fixture
    def client2(self, user2):
        c = APIClient()
        c.force_authenticate(user=user2)
        return c

    def test_cross_user_transaction_access_prevented(self, user1, user2, client2):
        cat1 = Category.objects.create(user=user1, name='Food')
        txn1 = Transaction.objects.create(
            user=user1, category=cat1, transaction_type=TransactionType.EXPENSE,
            amount=50.00, date=timezone.now().date()
        )

        detail_url = reverse('transactions:transaction-detail', kwargs={'pk': txn1.pk})
        res_get = client2.get(detail_url)
        assert res_get.status_code == status.HTTP_404_NOT_FOUND

        res_patch = client2.patch(detail_url, {'amount': '999.00'})
        assert res_patch.status_code == status.HTTP_404_NOT_FOUND

        res_del = client2.delete(detail_url)
        assert res_del.status_code == status.HTTP_404_NOT_FOUND

    def test_cross_user_category_access_prevented(self, user1, user2, client2):
        cat1 = Category.objects.create(user=user1, name='User1 Category')
        detail_url = reverse('transactions:category-detail', kwargs={'pk': cat1.pk})

        assert client2.get(detail_url).status_code == status.HTTP_404_NOT_FOUND
        assert client2.patch(detail_url, {'name': 'Hacked'}).status_code == status.HTTP_404_NOT_FOUND
        assert client2.delete(detail_url).status_code == status.HTTP_404_NOT_FOUND

    def test_cross_user_budget_access_prevented(self, user1, user2, client2):
        b1 = Budget.objects.create(
            user=user1, name='Groceries', amount=500.00, period=BudgetPeriod.MONTHLY,
            start_date=timezone.now().date(), end_date=timezone.now().date() + timedelta(days=30)
        )
        detail_url = reverse('transactions:budget-detail', kwargs={'pk': b1.pk})
        assert client2.get(detail_url).status_code == status.HTTP_404_NOT_FOUND

    def test_cross_user_financial_goal_access_prevented(self, user1, user2, client2):
        g1 = FinancialGoal.objects.create(
            user=user1, name='Car Fund', target_amount=10000.00, target_date=timezone.now().date() + timedelta(days=365)
        )
        detail_url = reverse('transactions:financial-goal-detail', kwargs={'pk': g1.pk})
        assert client2.get(detail_url).status_code == status.HTTP_404_NOT_FOUND

    def test_cross_user_recurring_transaction_access_prevented(self, user1, user2, client2):
        cat1 = Category.objects.create(user=user1, name='Rent Cat')
        r1 = RecurringTransaction.objects.create(
            user=user1, category=cat1, name='Rent', amount=1000.00,
            transaction_type=TransactionType.EXPENSE, frequency=RecurrenceFrequency.MONTHLY,
            start_date=timezone.now().date(), next_run_date=timezone.now().date()
        )
        detail_url = reverse('transactions:recurring-transaction-detail', kwargs={'pk': r1.pk})
        assert client2.get(detail_url).status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestImportExportSecurity:
    def test_import_rejects_non_csv_files(self, user):
        client = APIClient()
        client.force_authenticate(user=user)

        txt_file = io.BytesIO(b"date,description,amount\n2026-01-01,test,10")
        txt_file.name = "data.txt"

        url = reverse('transactions:import-transactions')
        response = client.post(url, {'file': txt_file}, format='multipart')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Only CSV files are supported" in str(response.data)

    def test_import_rejects_file_exceeding_5mb(self, user):
        client = APIClient()
        client.force_authenticate(user=user)

        large_file = io.BytesIO(b"0" * (5 * 1024 * 1024 + 1))
        large_file.name = "large.csv"

        url = reverse('transactions:import-transactions')
        response = client.post(url, {'file': large_file}, format='multipart')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "exceeds 5MB limit" in str(response.data)

    def test_import_rejects_file_exceeding_1000_rows(self, user):
        client = APIClient()
        client.force_authenticate(user=user)

        content = "date,description,amount,transaction_type,category\n"
        for i in range(1001):
            content += f"2026-01-01,item {i},10.00,EXPENSE,Groceries\n"

        csv_file = io.BytesIO(content.encode('utf-8'))
        csv_file.name = "too_many_rows.csv"

        url = reverse('transactions:import-transactions')
        response = client.post(url, {'file': csv_file}, format='multipart')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "contains more than 1000 rows" in str(response.data)


@pytest.mark.django_db
class TestSensitiveDataAndExceptionProtection:
    def test_exception_handler_scrubs_sensitive_credentials(self):
        from finance_tracker.exceptions import sanitize_error_data
        data = {
            'username': ['This field is required.'],
            'secret_key': ['Exposed key: 12345'],
            'db_password': ['Invalid password.']
        }
        cleaned = sanitize_error_data(data)
        assert cleaned['secret_key'] == ['Redacted for security.']
        assert cleaned['db_password'] == ['Redacted for security.']
        assert cleaned['username'] == ['This field is required.']


@pytest.mark.django_db
class TestProductionSettingsAndSystemChecks:
    def test_django_system_check_passes(self):
        out = io.StringIO()
        call_command('check', stdout=out)
        output = out.getvalue()
        assert "System check identified no issues" in output or output == ""
