import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from transactions.models import Category, Transaction
from transactions.choices import TransactionType

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestDay6HealthCheck:
    def test_health_check_returns_200_and_status(self, api_client):
        url = reverse('health-check')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get('status') == 'healthy'
        assert response.data.get('database') == 'connected'

    def test_health_check_unauthenticated_allowed(self, api_client):
        url = reverse('health-check')
        api_client.credentials()  # Unauthenticated
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestDay6AuthenticationHardening:
    @pytest.fixture
    def user(self):
        return User.objects.create_user(username='testuser', email='test@example.com', password='Password123!')

    def test_unauthenticated_access_denied(self, api_client):
        url = reverse('transactions:transaction-list-create')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_bearer_token_denied(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token_string')
        url = reverse('transactions:transaction-list-create')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_blacklisted_token_rejected(self, api_client, user):
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # Logout by blacklisting refresh token
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        logout_url = reverse('auth:logout')
        logout_res = api_client.post(logout_url, {'refresh': str(refresh)})
        assert logout_res.status_code == status.HTTP_200_OK

        # Trying to logout with same refresh token again fails
        re_logout_res = api_client.post(logout_url, {'refresh': str(refresh)})
        assert re_logout_res.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestDay6UserDataIsolationAndPermissions:
    @pytest.fixture
    def user_a(self):
        return User.objects.create_user(username='usera', email='usera@example.com', password='Password123!')

    @pytest.fixture
    def user_b(self):
        return User.objects.create_user(username='userb', email='userb@example.com', password='Password123!')

    @pytest.fixture
    def category_a(self, user_a):
        return Category.objects.create(user=user_a, name='User A Category')

    @pytest.fixture
    def transaction_a(self, user_a, category_a):
        return Transaction.objects.create(
            user=user_a,
            category=category_a,
            transaction_type=TransactionType.INCOME,
            amount='100.00',
            description='User A Income',
            date='2026-01-01'
        )

    def test_user_b_cannot_get_user_a_category(self, api_client, user_b, category_a):
        refresh = RefreshToken.for_user(user_b)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        url = reverse('transactions:category-detail', kwargs={'pk': category_a.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_user_b_cannot_update_user_a_category(self, api_client, user_b, category_a):
        refresh = RefreshToken.for_user(user_b)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        url = reverse('transactions:category-detail', kwargs={'pk': category_a.pk})
        response = api_client.patch(url, {'name': 'Hacked Category'})
        assert response.status_code == status.HTTP_404_NOT_FOUND
        category_a.refresh_from_db()
        assert category_a.name == 'User A Category'

    def test_user_b_cannot_delete_user_a_category(self, api_client, user_b, category_a):
        refresh = RefreshToken.for_user(user_b)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        url = reverse('transactions:category-detail', kwargs={'pk': category_a.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Category.objects.filter(pk=category_a.pk).exists()

    def test_user_b_cannot_get_user_a_transaction(self, api_client, user_b, transaction_a):
        refresh = RefreshToken.for_user(user_b)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        url = reverse('transactions:transaction-detail', kwargs={'pk': transaction_a.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_user_b_cannot_update_user_a_transaction(self, api_client, user_b, transaction_a):
        refresh = RefreshToken.for_user(user_b)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        url = reverse('transactions:transaction-detail', kwargs={'pk': transaction_a.pk})
        response = api_client.patch(url, {'amount': '9999.00'})
        assert response.status_code == status.HTTP_404_NOT_FOUND
        transaction_a.refresh_from_db()
        assert transaction_a.amount != 9999.00

    def test_user_b_cannot_delete_user_a_transaction(self, api_client, user_b, transaction_a):
        refresh = RefreshToken.for_user(user_b)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        url = reverse('transactions:transaction-detail', kwargs={'pk': transaction_a.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Transaction.objects.filter(pk=transaction_a.pk).exists()

    def test_user_b_cannot_use_user_a_category_on_create(self, api_client, user_b, category_a):
        refresh = RefreshToken.for_user(user_b)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        url = reverse('transactions:transaction-list-create')
        data = {
            'category': category_a.pk,
            'transaction_type': TransactionType.EXPENSE,
            'amount': '50.00',
            'description': 'Attempt cross-user category',
            'date': '2026-01-02'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestDay6QueryOptimization:
    def test_transaction_list_select_related_optimization(self, api_client, django_assert_num_queries):
        user = User.objects.create_user(username='optuser', email='opt@example.com', password='Password123!')
        cat1 = Category.objects.create(user=user, name='Cat 1')
        cat2 = Category.objects.create(user=user, name='Cat 2')
        for i in range(5):
            Transaction.objects.create(
                user=user,
                category=cat1 if i % 2 == 0 else cat2,
                transaction_type=TransactionType.EXPENSE,
                amount=f'{10 + i}.00',
                description=f'Txn {i}',
                date='2026-01-01'
            )

        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        url = reverse('transactions:transaction-list-create')

        # With select_related('category'), fetching transaction list should take minimal fixed queries (e.g., auth check + main query)
        with django_assert_num_queries(3):
            response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 5


@pytest.mark.django_db
class TestDay6SecurityHeadersAndConfig:
    def test_health_check_response_headers(self, api_client):
        url = reverse('health-check')
        response = api_client.get(url)
        assert response.get('X-Frame-Options') == 'DENY'
        assert response.get('X-Content-Type-Options') == 'nosniff'
