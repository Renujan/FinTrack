from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from transactions.choices import TransactionType
from transactions.models import Category, Transaction

User = get_user_model()


class TransactionListCreateAPITests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(email='user1@example.com', password='Password123!', username='user1')
        self.user2 = User.objects.create_user(email='user2@example.com', password='Password123!', username='user2')
        self.category1 = Category.objects.create(user=self.user1, name='Food')
        self.category2 = Category.objects.create(user=self.user2, name='Rent')

        self.list_url = reverse('transactions:transaction-list-create')
        self.cat_list_url = reverse('transactions:category-list-create')

    def test_unauthenticated_request_denied(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_user_transactions_only(self):
        Transaction.objects.create(
            user=self.user1,
            category=self.category1,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('50.00'),
            date='2026-08-12'
        )
        Transaction.objects.create(
            user=self.user2,
            category=self.category2,
            transaction_type=TransactionType.INCOME,
            amount=Decimal('1000.00'),
            date='2026-08-12'
        )

        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        self.assertEqual(len(results), 1)
        self.assertEqual(Decimal(str(results[0]['amount'])), Decimal('50.00'))

    def test_create_transaction_for_authenticated_user(self):
        self.client.force_authenticate(user=self.user1)
        data = {
            'category': self.category1.id,
            'transaction_type': TransactionType.INCOME,
            'amount': '250.00',
            'description': 'Freelance payment',
            'date': '2026-08-12'
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.filter(user=self.user1).count(), 1)
        txn = Transaction.objects.get(id=response.data['id'])
        self.assertEqual(txn.user, self.user1)

    def test_create_transaction_with_other_user_category_fails(self):
        self.client.force_authenticate(user=self.user1)
        data = {
            'category': self.category2.id,  # Category owned by user2
            'transaction_type': TransactionType.EXPENSE,
            'amount': '100.00',
            'date': '2026-08-12'
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TransactionDetailAPITests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(email='detail1@example.com', password='Password123!', username='detail1')
        self.user2 = User.objects.create_user(email='detail2@example.com', password='Password123!', username='detail2')
        self.category1 = Category.objects.create(user=self.user1, name='Groceries')
        self.category2 = Category.objects.create(user=self.user2, name='Utilities')

        self.txn1 = Transaction.objects.create(
            user=self.user1,
            category=self.category1,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('45.50'),
            description='Supermarket',
            date='2026-08-10'
        )
        self.detail_url_1 = reverse('transactions:transaction-detail', kwargs={'pk': self.txn1.pk})

    def test_get_detail_owner_success(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.detail_url_1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.txn1.id)

    def test_get_detail_cross_user_returns_404(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(self.detail_url_1)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_transaction_success(self):
        self.client.force_authenticate(user=self.user1)
        data = {
            'category': self.category1.id,
            'transaction_type': TransactionType.EXPENSE,
            'amount': '60.00',
            'description': 'Supermarket updated',
            'date': '2026-08-11'
        }
        response = self.client.put(self.detail_url_1, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.txn1.refresh_from_db()
        self.assertEqual(self.txn1.amount, Decimal('60.00'))

    def test_patch_transaction_success(self):
        self.client.force_authenticate(user=self.user1)
        data = {'description': 'Partially updated description'}
        response = self.client.patch(self.detail_url_1, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.txn1.refresh_from_db()
        self.assertEqual(self.txn1.description, 'Partially updated description')

    def test_delete_transaction_success(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(self.detail_url_1)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Transaction.objects.filter(pk=self.txn1.pk).exists())

    def test_update_cross_user_returns_404(self):
        self.client.force_authenticate(user=self.user2)
        data = {'description': 'Unauthorized update'}
        response = self.client.patch(self.detail_url_1, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_cross_user_returns_404(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.delete(self.detail_url_1)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Transaction.objects.filter(pk=self.txn1.pk).exists())
