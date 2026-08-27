from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    currency = models.CharField(
        max_length=10,
        default="LKR",
        help_text="Primary currency ISO code (e.g. LKR, USD, EUR, GBP, INR)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email if self.email else self.username


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('User')
    )
    display_name = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text=_('User display or screen name')
    )
    bio = models.TextField(
        blank=True,
        default='',
        help_text=_('Short bio or user description')
    )
    phone_number = models.CharField(
        max_length=30,
        blank=True,
        default='',
        help_text=_('Contact phone number')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')

    def __str__(self):
        return f"Profile of {self.user.username}"

    @property
    def full_name(self):
        name = f"{self.user.first_name} {self.user.last_name}".strip()
        return name if name else (self.display_name or self.user.username)

    @property
    def profile_updated_at(self):
        return self.updated_at


class DateFormatChoice(models.TextChoices):
    YYYY_MM_DD = 'YYYY-MM-DD', _('YYYY-MM-DD (e.g. 2026-08-27)')
    DD_MM_YYYY = 'DD/MM/YYYY', _('DD/MM/YYYY (e.g. 27/08/2026)')
    MM_DD_YYYY = 'MM/DD/YYYY', _('MM/DD/YYYY (e.g. 08/27/2026)')


class DefaultTransactionTypeChoice(models.TextChoices):
    EXPENSE = 'EXPENSE', _('Expense')
    INCOME = 'INCOME', _('Income')


SUPPORTED_CURRENCIES = [
    ('LKR', 'Sri Lankan Rupee (LKR)'),
    ('USD', 'US Dollar (USD)'),
    ('EUR', 'Euro (EUR)'),
    ('GBP', 'British Pound (GBP)'),
    ('INR', 'Indian Rupee (INR)'),
    ('CAD', 'Canadian Dollar (CAD)'),
    ('AUD', 'Australian Dollar (AUD)'),
    ('JPY', 'Japanese Yen (JPY)'),
]

CURRENCY_SYMBOLS = {
    'LKR': 'Rs.',
    'USD': '$',
    'EUR': '€',
    'GBP': '£',
    'INR': '₹',
    'CAD': 'CA$',
    'AUD': 'A$',
    'JPY': '¥',
}


class UserPreference(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='preferences',
        verbose_name=_('User')
    )
    # Currency Preferences
    currency = models.CharField(
        max_length=10,
        default='LKR',
        help_text=_('Preferred primary currency code (e.g. LKR, USD, EUR, GBP, INR)')
    )
    currency_symbol = models.CharField(
        max_length=10,
        default='Rs.',
        help_text=_('Display symbol for preferred currency')
    )
    default_currency = models.CharField(
        max_length=10,
        default='LKR',
        help_text=_('Default currency for transactions and budgets')
    )

    # Date & Time Preferences
    date_format = models.CharField(
        max_length=20,
        choices=DateFormatChoice.choices,
        default=DateFormatChoice.YYYY_MM_DD,
        help_text=_('Preferred date display format')
    )
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        help_text=_('User local timezone e.g. UTC, Asia/Colombo, America/New_York')
    )
    language = models.CharField(
        max_length=10,
        default='en',
        help_text=_('Preferred display language code')
    )

    # Financial Preferences
    financial_year_start_month = models.PositiveSmallIntegerField(
        default=1,
        help_text=_('Month when financial year begins (1=Jan to 12=Dec)')
    )
    default_transaction_type = models.CharField(
        max_length=10,
        choices=DefaultTransactionTypeChoice.choices,
        default=DefaultTransactionTypeChoice.EXPENSE,
        help_text=_('Default transaction type selected when creating entries')
    )

    # Notification Preferences
    budget_alerts = models.BooleanField(
        default=True,
        help_text=_('Receive notifications when budgets reach warning or exceeded thresholds')
    )
    goal_alerts = models.BooleanField(
        default=True,
        help_text=_('Receive notifications for financial goal progress and milestones')
    )
    recurring_transaction_alerts = models.BooleanField(
        default=True,
        help_text=_('Receive notifications for upcoming due or generated recurring transactions')
    )
    system_notifications = models.BooleanField(
        default=True,
        help_text=_('Receive general system and security notifications')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_preferences'
        verbose_name = _('User Preference')
        verbose_name_plural = _('User Preferences')

    def __str__(self):
        return f"Preferences of {self.user.username}"

    def save(self, *args, **kwargs):
        if self.currency in CURRENCY_SYMBOLS:
            self.currency_symbol = CURRENCY_SYMBOLS[self.currency]
        self.default_currency = self.currency
        super().save(*args, **kwargs)


@receiver(post_save, sender=User)
def create_user_profile_and_preferences(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
        UserPreference.objects.get_or_create(
            user=instance,
            defaults={
                'currency': instance.currency or 'LKR',
                'default_currency': instance.currency or 'LKR',
                'currency_symbol': CURRENCY_SYMBOLS.get(instance.currency, 'Rs.')
            }
        )

