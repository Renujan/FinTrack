from django.apps import AppConfig


class TransactionsConfig(AppConfig):
    """App configuration for transactions and category management module."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'transactions'
