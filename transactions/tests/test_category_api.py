from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from transactions.choices import TransactionType
from transactions.models import Category, Transaction

User = get_user_model()


class CategoryAPITests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(email='catuser1@example.com', password='Password123!', username='catuser1')
        self.user2 = User.objects.create_user(email='catuser2@example.com', password='Password123!', username='catuser2')

        self.cat1 = Category.objects.create(user=self.user1, name='Food')
        self.cat2 = Category.objects.create(user=self.user2, name='Transport')

        self.list_url = reverse('transactions:category-list-create')
        self.detail_url_1 = reverse('transactions:category-detail', kwargs={'pk': self.cat1.pk})
        self.detail_url_2 = reverse('transactions:category-detail', kwargs={'pk': self.cat2.pk})

    def test_unauthenticated_requests_denied(self):
        self.assertEqual(self.client.get(self.list_url).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.post(self.list_url, {'name': 'New'}).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.get(self.detail_url_1).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.put(self.detail_url_1, {'name': 'New'}).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.delete(self.detail_url_1).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_user_categories_only(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.cat1.id)

    def test_create_category_success(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.list_url, {'name': 'Utilities'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Utilities')
        self.assertTrue(Category.objects.filter(user=self.user1, name='Utilities').exists())

    def test_create_category_whitespace_trimmed(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.list_url, {'name': '   Salary   '})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Salary')

    def test_create_category_empty_name_fails(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.list_url, {'name': '   '})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)

    def test_create_category_duplicate_same_user_fails(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.list_url, {'name': 'food'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_category_same_name_different_users_allowed(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.list_url, {'name': 'Transport'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_retrieve_category_detail_success(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.detail_url_1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Food')

    def test_update_category_put(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.put(self.detail_url_1, {'name': 'Dining Out'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.cat1.refresh_from_db()
        self.assertEqual(self.cat1.name, 'Dining Out')

    def test_update_category_patch(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.patch(self.detail_url_1, {'name': 'Groceries & Dining'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.cat1.refresh_from_db()
        self.assertEqual(self.cat1.name, 'Groceries & Dining')

    def test_delete_category_unused_success(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(self.detail_url_1)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Category.objects.filter(pk=self.cat1.pk).exists())

    def test_delete_category_with_transactions_protected(self):
        Transaction.objects.create(
            user=self.user1,
            category=self.cat1,
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal('50.00'),
            date='2026-08-12'
        )
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(self.detail_url_1)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Cannot delete category', response.data.get('detail', ''))
        self.assertTrue(Category.objects.filter(pk=self.cat1.pk).exists())

    def test_cross_user_category_access_denied(self):
        self.client.force_authenticate(user=self.user1)
        self.assertEqual(self.client.get(self.detail_url_2).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.put(self.detail_url_2, {'name': 'Hacked'}).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.delete(self.detail_url_2).status_code, status.HTTP_404_NOT_FOUND)
