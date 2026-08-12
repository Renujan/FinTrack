import django_filters
from .models import Transaction


class TransactionFilter(django_filters.FilterSet):
    type = django_filters.CharFilter(field_name='transaction_type', lookup_expr='iexact')
    category = django_filters.CharFilter(method='filter_by_category')
    date = django_filters.DateFilter(field_name='date')
    start_date = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model = Transaction
        fields = ['type', 'category', 'date', 'start_date', 'end_date']

    def filter_by_category(self, queryset, name, value):
        if value.isdigit():
            return queryset.filter(category_id=int(value))
        return queryset.filter(category__name__iexact=value)
