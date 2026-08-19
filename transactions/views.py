from django.shortcuts import get_object_or_404
from django.db.models import ProtectedError, Case, When
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, filters, status, response
from rest_framework.views import APIView
from .filters import (
    TransactionFilter,
    BudgetFilter,
    RecurringTransactionFilter,
    FinancialGoalFilter,
    validate_filter_params,
    validate_budget_filter_params,
    validate_recurring_filter_params,
    validate_goal_filter_params,
)
from .models import Category, Transaction, Budget, RecurringTransaction, FinancialGoal
from .pagination import StandardResultsSetPagination, RecurringTransactionResultsSetPagination
from .permissions import IsOwner
from .serializers import (
    CategorySerializer,
    TransactionSerializer,
    BudgetSerializer,
    RecurringTransactionSerializer,
    FinancialGoalSerializer,
)
from .services import BudgetCalculationService, RecurringTransactionService, GoalCalculationService


class CategoryListCreateView(generics.ListCreateAPIView):
    """
    List and create categories for the authenticated user.
    Supports case-insensitive search by category name, ordering, and pagination.
    """
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """
        Enforce strict user data isolation by scoping category querysets to authenticated user.
        """
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update (PUT/PATCH), or delete a category owned by the authenticated user.
    Protects category deletion if associated transactions exist.
    """
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
        except ProtectedError:
            return response.Response(
                {'detail': 'Cannot delete category because it is being used by existing transactions.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return response.Response(status=status.HTTP_204_NO_CONTENT)


class TransactionListCreateView(generics.ListCreateAPIView):
    """
    List and create transactions for the authenticated user.
    Supports case-insensitive search across description and category name fields.
    """
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TransactionFilter
    search_fields = ['description', 'category__name']
    ordering_fields = ['date', 'amount', 'created_at']
    ordering = ['-date', '-created_at']
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """
        Enforce strict user data isolation and optimize database query with select_related('category').
        """
        return Transaction.objects.filter(user=self.request.user).select_related('category')

    def filter_queryset(self, queryset):
        """
        Applies filter parameter validation and custom field mappings for sorting (e.g. transaction_date -> date, amount, created_at).
        """
        validate_filter_params(self.request.query_params)

        ordering_param = self.request.query_params.get('ordering')
        if ordering_param:
            ordering_fields = [f.strip() for f in ordering_param.split(',') if f.strip()]
            mapped_ordering = []
            for field in ordering_fields:
                if field == 'transaction_date':
                    mapped_ordering.append('date')
                elif field == '-transaction_date':
                    mapped_ordering.append('-date')
                else:
                    mapped_ordering.append(field)

            for backend in list(self.filter_backends):
                if backend is filters.OrderingFilter:
                    continue
                queryset = backend().filter_queryset(self.request, queryset, self)

            return queryset.order_by(*mapped_ordering)

        return super().filter_queryset(queryset)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        """
        Enforce strict user data isolation and optimize database query with select_related('category').
        """
        return Transaction.objects.filter(user=self.request.user).select_related('category')


class BudgetListCreateView(generics.ListCreateAPIView):
    """
    List and create budgets for the authenticated user.
    Supports search across budget name and category name, filtering, ordering, and pagination.
    """
    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = BudgetFilter
    search_fields = ['name', 'category__name']
    ordering_fields = ['start_date', 'end_date', 'amount', 'created_at', 'name']
    ordering = ['-start_date', '-created_at']
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """
        Enforce strict user data isolation and optimize query with select_related('category').
        """
        return Budget.objects.filter(user=self.request.user).select_related('category')

    def filter_queryset(self, queryset):
        """
        Applies query parameter validation and custom sorting logic for budgets.
        """
        validate_budget_filter_params(self.request.query_params)

        ordering_param = self.request.query_params.get('ordering')
        if ordering_param and ('percentage_used' in ordering_param or '-percentage_used' in ordering_param):
            for backend in list(self.filter_backends):
                if backend is filters.OrderingFilter:
                    continue
                queryset = backend().filter_queryset(self.request, queryset, self)

            items = list(queryset)
            reverse = '-percentage_used' in ordering_param
            items.sort(
                key=lambda b: BudgetCalculationService.calculate_budget_metrics(b)['percentage_used'],
                reverse=reverse
            )
            ids = [b.id for b in items]
            if not ids:
                return queryset.none()
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(ids)])
            return Budget.objects.filter(pk__in=ids).order_by(preserved)

        return super().filter_queryset(queryset)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BudgetDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update (PUT/PATCH), or delete a budget owned by the authenticated user.
    """
    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user).select_related('category')


class RecurringTransactionListCreateView(generics.ListCreateAPIView):
    """
    List and create recurring transactions for the authenticated user.
    Supports search across name, description, and category name, filtering, ordering, and pagination.
    """
    serializer_class = RecurringTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = RecurringTransactionFilter
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['amount', 'start_date', 'next_run_date', 'created_at', 'frequency', 'name']
    ordering = ['next_run_date', '-created_at']
    pagination_class = RecurringTransactionResultsSetPagination

    def get_queryset(self):
        """
        Enforce strict user data isolation and optimize database query with select_related('category').
        """
        return RecurringTransaction.objects.filter(user=self.request.user).select_related('category')

    def filter_queryset(self, queryset):
        """
        Applies filter parameter validation for recurring transactions before executing backend queries.
        """
        validate_recurring_filter_params(self.request.query_params)
        return super().filter_queryset(queryset)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RecurringTransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update (PUT/PATCH), or delete a recurring transaction owned by the authenticated user.
    """
    serializer_class = RecurringTransactionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return RecurringTransaction.objects.filter(user=self.request.user).select_related('category')


class RecurringTransactionPauseView(APIView):
    """
    Pause an active recurring transaction schedule for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        recurring_tx = get_object_or_404(RecurringTransaction, pk=pk, user=request.user)
        paused_tx = RecurringTransactionService.pause_schedule(recurring_tx)
        serializer = RecurringTransactionSerializer(paused_tx, context={'request': request})
        return response.Response(serializer.data, status=status.HTTP_200_OK)


class RecurringTransactionResumeView(APIView):
    """
    Resume a paused recurring transaction schedule for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        recurring_tx = get_object_or_404(RecurringTransaction, pk=pk, user=request.user)
        resumed_tx = RecurringTransactionService.resume_schedule(recurring_tx)
        serializer = RecurringTransactionSerializer(resumed_tx, context={'request': request})
        return response.Response(serializer.data, status=status.HTTP_200_OK)


class FinancialGoalListCreateView(generics.ListCreateAPIView):
    """
    List and create financial goals for the authenticated user.
    Supports search across goal name, description, and category name, filtering, ordering, and pagination.
    """
    serializer_class = FinancialGoalSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = FinancialGoalFilter
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['target_amount', 'target_date', 'created_at', 'name']
    ordering = ['target_date', '-created_at']
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """
        Enforce strict user data isolation and optimize database query with select_related('category').
        """
        return FinancialGoal.objects.filter(user=self.request.user).select_related('category')

    def filter_queryset(self, queryset):
        """
        Applies filter parameter validation and custom ordering for goal calculation metrics.
        """
        validate_goal_filter_params(self.request.query_params)

        ordering_param = self.request.query_params.get('ordering')
        if ordering_param and ('percentage_complete' in ordering_param or '-percentage_complete' in ordering_param or 'progress_percentage' in ordering_param or '-progress_percentage' in ordering_param):
            for backend in list(self.filter_backends):
                if backend is filters.OrderingFilter:
                    continue
                queryset = backend().filter_queryset(self.request, queryset, self)

            items = list(queryset)
            reverse = '-percentage_complete' in ordering_param or '-progress_percentage' in ordering_param
            items.sort(
                key=lambda g: GoalCalculationService.calculate_goal_metrics(g)['percentage_complete'],
                reverse=reverse
            )
            ids = [g.id for g in items]
            if not ids:
                return queryset.none()
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(ids)])
            return FinancialGoal.objects.filter(pk__in=ids).order_by(preserved)

        return super().filter_queryset(queryset)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FinancialGoalDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update (PUT/PATCH), or delete a financial goal owned by the authenticated user.
    """
    serializer_class = FinancialGoalSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return FinancialGoal.objects.filter(user=self.request.user).select_related('category')


class FinancialGoalPauseView(APIView):
    """
    Pause an active financial goal for the authenticated user.
    Updates goal status to PAUSED while preserving accumulated contributions.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        goal = get_object_or_404(FinancialGoal, pk=pk, user=request.user)
        if goal.is_active:
            goal.is_active = False
            goal.save(update_fields=['is_active', 'updated_at'])
        serializer = FinancialGoalSerializer(goal, context={'request': request})
        return response.Response(serializer.data, status=status.HTTP_200_OK)


class FinancialGoalResumeView(APIView):
    """
    Resume a paused financial goal for the authenticated user.
    Restores active goal monitoring and status recalculation.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        goal = get_object_or_404(FinancialGoal, pk=pk, user=request.user)
        if not goal.is_active:
            goal.is_active = True
            goal.save(update_fields=['is_active', 'updated_at'])
        serializer = FinancialGoalSerializer(goal, context={'request': request})
        return response.Response(serializer.data, status=status.HTTP_200_OK)


