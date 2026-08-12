from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from transactions.choices import TransactionType
from transactions.models import Category, Transaction
from transactions.serializers import CategorySerializer, TransactionSerializer

User = get_user_model()


class SerializerTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user1 = User.objects.create_user(email='user1@example.com', password='Password123!', username='user1')
        self.user2 = User.objects.create_user(email='user2@example.com', password='Password123!', username='user2')
        self.category1 = Category.objects.create(user=self.user1, name='Food')
        self.category2 = Category.objects.create(user=self.user2, name='Transport')

    def test_category_serializer_duplicate_prevention(self):
        request = self.factory.get('/')
        request.user = self.user1
        serializer = CategorySerializer(data={'name': 'Food'}, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_category_serializer_allowed_for_different_user(self):
        request = self.factory.get('/')
        request.user = self.user2
        serializer = CategorySerializer(data={'name': 'Food'}, context={'request': request})
        self.assertTrue(serializer.is_valid())

    def test_transaction_serializer_validation(self):
        request = self.factory.get('/')
        request.user = self.user1
        data = {
            'category': self.category1.id,
            'transaction_type': TransactionType.EXPENSE,
            'amount': '50.00',
            'description': 'Lunch',
            'date': '2026-08-12'
        }
        serializer = TransactionSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_transaction_serializer_invalid_amount(self):
        request = self.factory.get('/')
        request.user = self.user1
        data = {
            'category': self.category1.id,
            'transaction_type': TransactionType.EXPENSE,
            'amount': '-10.00',
            'description': 'Invalid',
            'date': '2026-08-12'
        }
        serializer = TransactionSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('amount', serializer.errors)

    def test_transaction_serializer_cross_user_category(self):
        request = self.factory.get('/')
        request.user = self.user1
        data = {
            'category': self.category2.id,
            'transaction_type': TransactionType.EXPENSE,
            'amount': '25.00',
            'description': 'Hacking',
            'date': '2026-08-12'
        }
        serializer = TransactionSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('category', serializer.errors)
