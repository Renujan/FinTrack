from django.apps import apps
from django.test import TestCase
from transactions.apps import TransactionsConfig


class TransactionsConfigTest(TestCase):
    def test_apps_config(self):
        self.assertEqual(TransactionsConfig.name, 'transactions')
        self.assertEqual(apps.get_app_config('transactions').name, 'transactions')
