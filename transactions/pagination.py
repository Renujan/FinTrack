from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination for Transaction API querysets with configurable page size (default 10)
    and maximum limit of 100 per page.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class CategoryResultsSetPagination(PageNumberPagination):
    """
    Pagination configuration specifically tailored for Category list endpoints.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class BudgetResultsSetPagination(PageNumberPagination):
    """
    Pagination configuration specifically tailored for Budget list endpoints.
    Default page size is 10, max page size is 100.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class RecurringTransactionResultsSetPagination(PageNumberPagination):
    """
    Pagination configuration specifically tailored for RecurringTransaction list endpoints.
    Default page size is 10, max page size is 100.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class NotificationResultsSetPagination(PageNumberPagination):
    """
    Pagination configuration specifically tailored for Notification list endpoints.
    Default page size is 10, max page size is 100.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100




