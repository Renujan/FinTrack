import logging
from users.models import UserPreference, CURRENCY_SYMBOLS, SUPPORTED_CURRENCIES

logger = logging.getLogger(__name__)


class UserPreferenceService:
    """
    Service layer for centralized user preference retrieval, modification,
    currency management, and notification delivery filtering.
    """

    @classmethod
    def get_preferences(cls, user):
        """
        Retrieves or creates the UserPreference object for the specified user.
        """
        if not user or not user.is_authenticated:
            return None
        preferences, _ = UserPreference.objects.get_or_create(
            user=user,
            defaults={
                'currency': getattr(user, 'currency', 'LKR') or 'LKR',
                'default_currency': getattr(user, 'currency', 'LKR') or 'LKR',
                'currency_symbol': CURRENCY_SYMBOLS.get(getattr(user, 'currency', 'LKR'), 'Rs.')
            }
        )
        return preferences

    @classmethod
    def update_preferences(cls, user, data):
        """
        Updates user preferences with sanitized values and keeps User.currency synchronized.
        """
        preferences = cls.get_preferences(user)
        if not preferences:
            return None

        for field in [
            'currency', 'currency_symbol', 'default_currency', 'date_format',
            'timezone', 'language', 'financial_year_start_month',
            'default_transaction_type', 'budget_alerts', 'goal_alerts',
            'recurring_transaction_alerts', 'system_notifications'
        ]:
            if field in data:
                setattr(preferences, field, data[field])

        # If currency updated, keep User.currency in sync
        if 'currency' in data:
            new_currency = data['currency']
            user.currency = new_currency
            user.save(update_fields=['currency', 'updated_at'])

        preferences.save()
        return preferences

    @classmethod
    def get_currency(cls, user):
        """
        Returns preferred currency code for the user (defaults to 'LKR').
        """
        preferences = cls.get_preferences(user)
        if preferences and preferences.currency:
            return preferences.currency
        return getattr(user, 'currency', 'LKR') or 'LKR'

    @classmethod
    def get_timezone(cls, user):
        """
        Returns preferred timezone string for the user (defaults to 'UTC').
        """
        preferences = cls.get_preferences(user)
        if preferences and preferences.timezone:
            return preferences.timezone
        return 'UTC'

    @classmethod
    def get_date_format(cls, user):
        """
        Returns preferred date format string for the user (defaults to 'YYYY-MM-DD').
        """
        preferences = cls.get_preferences(user)
        if preferences and preferences.date_format:
            return preferences.date_format
        return 'YYYY-MM-DD'

    @classmethod
    def validate_date_format(cls, date_format_str):
        from users.models import DateFormatChoice
        return date_format_str in DateFormatChoice.values

    @classmethod
    def get_financial_year_start_month(cls, user):
        preferences = cls.get_preferences(user)
        if preferences and preferences.financial_year_start_month:
            return preferences.financial_year_start_month
        return 1

    @classmethod
    def get_financial_preferences(cls, user):
        """
        Returns dictionary of user financial configuration settings.
        """
        preferences = cls.get_preferences(user)
        if not preferences:
            return {
                'default_currency': 'LKR',
                'currency_symbol': 'Rs.',
                'financial_year_start_month': 1,
                'default_transaction_type': 'EXPENSE'
            }
        return {
            'default_currency': preferences.default_currency,
            'currency_symbol': preferences.currency_symbol,
            'financial_year_start_month': preferences.financial_year_start_month,
            'default_transaction_type': preferences.default_transaction_type
        }

    @classmethod
    def should_receive_notification(cls, user, notification_type):
        """
        Evaluates whether a notification of notification_type should be created/sent
        based on user's notification preferences.
        """
        if not user or not getattr(user, 'is_authenticated', False):
            return True

        preferences = cls.get_preferences(user)
        if not preferences:
            return True

        from transactions.choices import NotificationType

        if notification_type in [NotificationType.BUDGET_EXCEEDED, NotificationType.BUDGET_WARNING]:
            return preferences.budget_alerts
        elif notification_type in [NotificationType.GOAL_COMPLETED, NotificationType.GOAL_WARNING]:
            return preferences.goal_alerts
        elif notification_type in [
            NotificationType.RECURRING_DUE,
            NotificationType.RECURRING_GENERATED,
            NotificationType.RECURRING_EXPIRED
        ]:
            return preferences.recurring_transaction_alerts

    @classmethod
    def get_preference_summary(cls, user):
        """
        Returns structured summary dictionary of all preferences for account overview.
        """
        preferences = cls.get_preferences(user)
        if not preferences:
            return cls.get_financial_preferences(user)
        return {
            'currency': preferences.currency,
            'currency_symbol': preferences.currency_symbol,
            'date_format': preferences.date_format,
            'timezone': preferences.timezone,
            'language': preferences.language,
            'financial_year_start_month': preferences.financial_year_start_month,
            'default_transaction_type': preferences.default_transaction_type,
            'budget_alerts': preferences.budget_alerts,
            'goal_alerts': preferences.goal_alerts,
            'recurring_transaction_alerts': preferences.recurring_transaction_alerts,
            'system_notifications': preferences.system_notifications,
        }
