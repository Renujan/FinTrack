import datetime
from django.db.models import Q
from rest_framework import serializers
from transactions.models import Transaction


def parse_report_dates(params):
    """
    Parses and validates start_date and end_date query parameters.
    Returns a tuple of (start_date_obj, end_date_obj).
    Raises DRF ValidationError if dates are malformed or start_date > end_date.
    """
    start_date = None
    end_date = None
    errors = {}

    start_str = params.get('start_date') if hasattr(params, 'get') else None
    if start_str:
        try:
            start_date = datetime.datetime.strptime(str(start_str), '%Y-%m-%d').date()
        except ValueError:
            errors['start_date'] = ["Invalid date format for start_date. Expected YYYY-MM-DD."]

    end_str = params.get('end_date') if hasattr(params, 'get') else None
    if end_str:
        try:
            end_date = datetime.datetime.strptime(str(end_str), '%Y-%m-%d').date()
        except ValueError:
            errors['end_date'] = ["Invalid date format for end_date. Expected YYYY-MM-DD."]

    if start_date and end_date and start_date > end_date:
        errors['start_date'] = ["start_date cannot be greater than end_date."]

    if errors:
        raise serializers.ValidationError(errors)

    return start_date, end_date


def get_user_transactions(user, start_date=None, end_date=None, category=None, transaction_type=None, search=None):
    """
    Returns user-scoped transaction queryset with select_related('category'),
    filtered by optional start_date, end_date, category, transaction_type, and search text.
    """
    qs = Transaction.objects.filter(user=user).select_related('category')

    if start_date:
        qs = qs.filter(date__gte=start_date)
    if end_date:
        qs = qs.filter(date__lte=end_date)
    if transaction_type:
        qs = qs.filter(transaction_type=transaction_type)
    if category:
        if isinstance(category, int) or (isinstance(category, str) and category.isdigit()):
            qs = qs.filter(category_id=int(category))
        else:
            qs = qs.filter(category__name__iexact=str(category))
    if search:
        qs = qs.filter(
            Q(description__icontains=search) | Q(category__name__icontains=search)
        )

    return qs
