from django.shortcuts import get_object_or_404
from django.db.models import ProtectedError, Case, When
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, filters, status, response, serializers
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from .filters import (
    TransactionFilter,
    BudgetFilter,
    RecurringTransactionFilter,
    FinancialGoalFilter,
    NotificationFilter,
    AuditLogFilter,
    validate_filter_params,
    validate_budget_filter_params,
    validate_recurring_filter_params,
    validate_goal_filter_params,
    validate_notification_filter_params,
    validate_audit_filter_params,
)
from .models import Category, Transaction, Budget, RecurringTransaction, RecurringTransactionExecution, FinancialGoal, GoalContribution, Notification, AuditLog
from .pagination import (
    StandardResultsSetPagination,
    RecurringTransactionResultsSetPagination,
    NotificationResultsSetPagination,
    AuditLogResultsSetPagination,
)
from .permissions import IsOwner
from .serializers import (
    CategorySerializer,
    TransactionSerializer,
    BudgetSerializer,
    RecurringTransactionSerializer,
    RecurringTransactionExecutionSerializer,
    FinancialGoalSerializer,
    GoalContributionSerializer,
    GoalProgressForecastSerializer,
    FinancialGoalSummarySerializer,
    NotificationSerializer,
    NotificationUpdateSerializer,
    AuditLogSerializer,
)
from .services import BudgetCalculationService, RecurringTransactionService, GoalCalculationService, FinancialGoalService, NotificationService
from .audit_services import AuditLogService
from subscriptions.services import SubscriptionService


@extend_schema(
    tags=['Categories'],
    summary='List or Create Income/Expense Categories',
    description='Retrieves custom and system categories or creates a new user category subject to subscription limit checks.',
    responses={
        200: CategorySerializer(many=True),
        201: CategorySerializer,
        400: OpenApiResponse(description='Validation error or invalid payload'),
        402: OpenApiResponse(description='Category creation limit exceeded for active subscription plan'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
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
        SubscriptionService.can_create_category(self.request.user)
        instance = serializer.save(user=self.request.user)
        AuditLogService.log_create(self.request.user, 'Category', instance.id, metadata={'name': instance.name}, request=self.request)


@extend_schema(
    tags=['Categories'],
    summary='Retrieve, Update, or Delete Category',
    description='Retrieves, updates, or deletes a category owned by the authenticated user. Deletion is blocked if referenced by active transactions.',
    responses={
        200: CategorySerializer,
        400: OpenApiResponse(description='Cannot delete category because it is being used by existing transactions.'),
        401: OpenApiResponse(description='Authentication required'),
        404: OpenApiResponse(description='Category not found'),
    }
)
class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):

    """
    Retrieve, update (PUT/PATCH), or delete a category owned by the authenticated user.
    Protects category deletion if associated transactions exist.
    """
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        instance = serializer.save()
        AuditLogService.log_update(self.request.user, 'Category', instance.id, metadata={'name': instance.name}, request=self.request)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        cat_id = instance.id
        cat_name = instance.name
        try:
            self.perform_destroy(instance)
            AuditLogService.log_delete(request.user, 'Category', cat_id, metadata={'name': cat_name}, request=request)
        except ProtectedError:
            return response.Response(
                {'detail': 'Cannot delete category because it is being used by existing transactions.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return response.Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=['Transactions'],
    summary='List or Create Transactions',
    description='Retrieves a paginated list of transactions filtered by date range, category, type, amount, or creates a new transaction.',
    responses={
        200: TransactionSerializer(many=True),
        201: TransactionSerializer,
        400: OpenApiResponse(description='Validation error or invalid query parameters'),
        402: OpenApiResponse(description='Transaction creation limit reached for active subscription plan'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
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
        SubscriptionService.can_create_transaction(self.request.user)
        instance = serializer.save(user=self.request.user)
        AuditLogService.log_create(self.request.user, 'Transaction', instance.id, metadata={'amount': str(instance.amount), 'type': instance.transaction_type}, request=self.request)


@extend_schema(
    tags=['Transactions'],
    summary='Retrieve, Update, or Delete Transaction',
    description='Retrieves, updates, or deletes a specific transaction owned by the authenticated user.',
    responses={
        200: TransactionSerializer,
        400: OpenApiResponse(description='Validation error'),
        401: OpenApiResponse(description='Authentication required'),
        404: OpenApiResponse(description='Transaction not found'),
    }
)
class TransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        """
        Enforce strict user data isolation and optimize database query with select_related('category').
        """
        return Transaction.objects.filter(user=self.request.user).select_related('category')

    def perform_update(self, serializer):
        instance = serializer.save()
        AuditLogService.log_update(self.request.user, 'Transaction', instance.id, metadata={'amount': str(instance.amount), 'type': instance.transaction_type}, request=self.request)

    def perform_destroy(self, instance):
        txn_id = instance.id
        meta = {'amount': str(instance.amount), 'type': instance.transaction_type}
        super().perform_destroy(instance)
        AuditLogService.log_delete(self.request.user, 'Transaction', txn_id, metadata=meta, request=self.request)


@extend_schema(
    tags=['Budgets'],
    summary='List or Create Category Budgets',
    description='Retrieves a list of spending budgets with progress metrics or creates a new budget.',
    responses={
        200: BudgetSerializer(many=True),
        201: BudgetSerializer,
        400: OpenApiResponse(description='Validation error or invalid query params'),
        402: OpenApiResponse(description='Budget creation limit reached for active subscription plan'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
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
        SubscriptionService.can_create_budget(self.request.user)
        instance = serializer.save(user=self.request.user)
        AuditLogService.log_create(self.request.user, 'Budget', instance.id, metadata={'name': instance.name, 'amount': str(instance.amount)}, request=self.request)


@extend_schema(
    tags=['Budgets'],
    summary='Retrieve, Update, or Delete Budget',
    description='Retrieves, updates, or deletes a specific budget owned by the authenticated user.',
    responses={
        200: BudgetSerializer,
        400: OpenApiResponse(description='Validation error'),
        401: OpenApiResponse(description='Authentication required'),
        404: OpenApiResponse(description='Budget not found'),
    }
)
class BudgetDetailView(generics.RetrieveUpdateDestroyAPIView):

    """
    Retrieve, update (PUT/PATCH), or delete a budget owned by the authenticated user.
    """
    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user).select_related('category')

    def perform_update(self, serializer):
        instance = serializer.save()
        AuditLogService.log_update(self.request.user, 'Budget', instance.id, metadata={'name': instance.name, 'amount': str(instance.amount)}, request=self.request)

    def perform_destroy(self, instance):
        b_id = instance.id
        meta = {'name': instance.name, 'amount': str(instance.amount)}
        super().perform_destroy(instance)
        AuditLogService.log_delete(self.request.user, 'Budget', b_id, metadata=meta, request=self.request)


@extend_schema(
    tags=['Recurring Transactions'],
    summary='List or Create Recurring Schedules',
    description='Retrieves a list of automated recurring income/expense schedules or creates a new schedule.',
    responses={
        200: RecurringTransactionSerializer(many=True),
        201: RecurringTransactionSerializer,
        400: OpenApiResponse(description='Validation error or invalid query params'),
        402: OpenApiResponse(description='Recurring schedule creation limit reached'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
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
        SubscriptionService.can_create_recurring_transaction(self.request.user)
        instance = serializer.save(user=self.request.user)
        AuditLogService.log_create(self.request.user, 'RecurringTransaction', instance.id, metadata={'name': instance.name, 'amount': str(instance.amount)}, request=self.request)


@extend_schema(
    tags=['Recurring Transactions'],
    summary='Retrieve, Update, or Delete Recurring Schedule',
    description='Retrieves, updates, or deletes a specific recurring transaction schedule owned by the authenticated user.',
    responses={
        200: RecurringTransactionSerializer,
        400: OpenApiResponse(description='Validation error'),
        401: OpenApiResponse(description='Authentication required'),
        404: OpenApiResponse(description='Recurring transaction not found'),
    }
)
class RecurringTransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update (PUT/PATCH), or delete a recurring transaction owned by the authenticated user.
    """
    serializer_class = RecurringTransactionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return RecurringTransaction.objects.filter(user=self.request.user).select_related('category')

    def perform_update(self, serializer):
        instance = serializer.save()
        AuditLogService.log_update(self.request.user, 'RecurringTransaction', instance.id, metadata={'name': instance.name}, request=self.request)

    def perform_destroy(self, instance):
        r_id = instance.id
        meta = {'name': instance.name}
        super().perform_destroy(instance)
        AuditLogService.log_delete(self.request.user, 'RecurringTransaction', r_id, metadata=meta, request=self.request)


@extend_schema(
    tags=['Recurring Transactions'],
    summary='Pause Recurring Schedule',
    description='Pauses execution of a recurring transaction schedule without deleting it.',
    request=None,
    responses={
        200: RecurringTransactionSerializer,
        401: OpenApiResponse(description='Authentication required'),
        404: OpenApiResponse(description='Recurring transaction schedule not found'),
    }
)
class RecurringTransactionPauseView(APIView):
    """
    Pause an active recurring transaction schedule for the authenticated user.
    Prevents future automated transaction generation while preserving schedule metadata.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        recurring_tx = get_object_or_404(RecurringTransaction, pk=pk, user=request.user)
        paused_tx = RecurringTransactionService.pause_schedule(recurring_tx, request=request)
        serializer = RecurringTransactionSerializer(paused_tx, context={'request': request})
        return response.Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Recurring Transactions'],
    summary='Resume Recurring Schedule',
    description='Resumes execution of a previously paused recurring transaction schedule.',
    request=None,
    responses={
        200: RecurringTransactionSerializer,
        401: OpenApiResponse(description='Authentication required'),
        404: OpenApiResponse(description='Recurring transaction schedule not found'),
    }
)
class RecurringTransactionResumeView(APIView):
    """
    Resume a paused recurring transaction schedule for the authenticated user.
    Validates next_run_date and marks recurrence schedule active.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        recurring_tx = get_object_or_404(RecurringTransaction, pk=pk, user=request.user)
        resumed_tx = RecurringTransactionService.resume_schedule(recurring_tx, request=request)
        serializer = RecurringTransactionSerializer(resumed_tx, context={'request': request})
        return response.Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Recurring Transactions'],
    summary='Execute Recurring Schedule Manually',
    description='Triggers immediate manual execution of a recurring transaction schedule, creating a transaction record and advancing schedule metadata.',
    request=None,
    responses={
        200: inline_serializer(
            name='RecurringExecutionResponse',
            fields={
                'detail': serializers.CharField(),
                'transaction': TransactionSerializer(),
                'recurring_transaction': RecurringTransactionSerializer(),
            }
        ),
        400: OpenApiResponse(description='Schedule paused, invalid, or already executed'),
        401: OpenApiResponse(description='Authentication required'),
        404: OpenApiResponse(description='Recurring transaction schedule not found'),
    }
)
class RecurringTransactionExecuteView(APIView):
    """
    Manually execute a recurring transaction schedule immediately for the authenticated user.
    Creates normal transaction record, updates execution history, and advances next run date.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        recurring_tx = get_object_or_404(RecurringTransaction, pk=pk, user=request.user)
        if not recurring_tx.is_active:
            return response.Response(
                {"detail": "Cannot execute a paused or inactive recurring transaction schedule."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            txn, updated_tx = RecurringTransactionService.execute_now(recurring_tx, request=request)
            txn_data = TransactionSerializer(txn, context={'request': request}).data
            recurring_data = RecurringTransactionSerializer(updated_tx, context={'request': request}).data
            return response.Response(
                {
                    "detail": "Recurring transaction executed successfully.",
                    "transaction": txn_data,
                    "recurring_transaction": recurring_data
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return response.Response(
                {"detail": f"Execution failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(
    tags=['Recurring Transactions'],
    summary='List Recurring Schedule Execution History',
    description='Retrieves execution history records for a specific recurring transaction schedule owned by the authenticated user.',
    responses={
        200: RecurringTransactionExecutionSerializer(many=True),
        401: OpenApiResponse(description='Authentication required'),
        404: OpenApiResponse(description='Recurring transaction schedule not found'),
    }
)
class RecurringTransactionHistoryView(generics.ListAPIView):
    """
    List execution history entries for a specific recurring transaction schedule owned by the authenticated user.
    Supports pagination and displays execution status (SUCCESS, FAILED, SKIPPED).
    """
    serializer_class = RecurringTransactionExecutionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = RecurringTransactionResultsSetPagination

    def get_queryset(self):
        recurring_tx = get_object_or_404(RecurringTransaction, pk=self.kwargs.get('pk'), user=self.request.user)
        return RecurringTransactionExecution.objects.filter(recurring_transaction=recurring_tx).select_related('recurring_transaction', 'transaction')


@extend_schema(
    tags=['Financial Goals'],
    summary='List or Create Financial Savings Goals',
    description='Retrieves a list of financial goals with target calculations and completion progress or creates a new goal.',
    responses={
        200: FinancialGoalSerializer(many=True),
        201: FinancialGoalSerializer,
        400: OpenApiResponse(description='Validation error or invalid query parameters'),
        402: OpenApiResponse(description='Financial goal limit reached'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
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
    ordering_fields = ['target_amount', 'current_amount', 'target_date', 'created_at', 'name', 'priority', 'status', 'goal_type']
    ordering = ['target_date', '-created_at']
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return FinancialGoal.objects.filter(user=self.request.user).select_related('category')

    def filter_queryset(self, queryset):
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
                key=lambda g: FinancialGoalService.calculate_percentage(g),
                reverse=reverse
            )
            ids = [g.id for g in items]
            if not ids:
                return queryset.none()
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(ids)])
            return FinancialGoal.objects.filter(pk__in=ids).order_by(preserved)

        return super().filter_queryset(queryset)

    def perform_create(self, serializer):
        SubscriptionService.can_create_goal(self.request.user)
        instance = FinancialGoalService.create_goal(
            user=self.request.user,
            data=serializer.validated_data,
            request=self.request
        )
        serializer.instance = instance


@extend_schema(
    tags=['Financial Goals'],
    summary='Retrieve, Update, or Delete Financial Goal',
    description='Retrieves, updates, or deletes a specific financial goal owned by the authenticated user.',
    responses={
        200: FinancialGoalSerializer,
        400: OpenApiResponse(description='Validation error'),
        401: OpenApiResponse(description='Authentication required'),
        404: OpenApiResponse(description='Goal not found'),
    }
)
class FinancialGoalDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update (PUT/PATCH), or delete a financial goal owned by the authenticated user.
    """
    serializer_class = FinancialGoalSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return FinancialGoal.objects.filter(user=self.request.user).select_related('category')

    def perform_update(self, serializer):
        instance = FinancialGoalService.update_goal(
            goal=self.get_object(),
            data=serializer.validated_data,
            request=self.request
        )
        serializer.instance = instance

    def perform_destroy(self, instance):
        g_id = instance.id
        meta = {'name': instance.name}
        super().perform_destroy(instance)
        AuditLogService.log_delete(self.request.user, 'FinancialGoal', g_id, metadata=meta, request=self.request)


@extend_schema(
    tags=['Financial Goals'],
    summary='List or Create Goal Contributions',
    description='Lists contributions made towards a goal or adds a new contribution.',
    responses={
        200: GoalContributionSerializer(many=True),
        201: GoalContributionSerializer,
        400: OpenApiResponse(description='Validation error'),
        401: OpenApiResponse(description='Authentication required'),
        404: OpenApiResponse(description='Goal not found'),
    }
)
class GoalContributionListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        goal = get_object_or_404(FinancialGoal, pk=pk, user=request.user)
        contributions = goal.contributions.all()
        serializer = GoalContributionSerializer(contributions, many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, pk):
        goal = get_object_or_404(FinancialGoal, pk=pk, user=request.user)
        serializer = GoalContributionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contribution = FinancialGoalService.add_contribution(
            goal=goal,
            amount=serializer.validated_data['amount'],
            note=serializer.validated_data.get('note', ''),
            contribution_date=serializer.validated_data.get('contribution_date'),
            user=request.user,
            request=request
        )
        res_serializer = GoalContributionSerializer(contribution)
        return response.Response(res_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['Financial Goals'],
    summary='Delete Goal Contribution',
    description='Removes a contribution made towards a goal and recalculates current goal amount.',
    responses={
        204: OpenApiResponse(description='Contribution deleted'),
        401: OpenApiResponse(description='Authentication required'),
        404: OpenApiResponse(description='Goal or contribution not found'),
    }
)
class GoalContributionDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, goal_pk, pk):
        goal = get_object_or_404(FinancialGoal, pk=goal_pk, user=request.user)
        contribution = get_object_or_404(GoalContribution, pk=pk, goal=goal)
        FinancialGoalService.remove_contribution(contribution, user=request.user, request=request)
        return response.Response(status=status.HTTP_204_NO_CONTENT)




@extend_schema(
    tags=['Notifications'],
    summary='List Notifications',
    description='Retrieves a paginated list of user notifications with filter parameters.',
    responses={
        200: NotificationSerializer(many=True),
        400: OpenApiResponse(description='Invalid query parameters'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class NotificationListView(generics.ListAPIView):
    """
    List notifications for the authenticated user.
    Supports filtering by is_read, notification_type, created_at date range, search, ordering, and pagination.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = NotificationFilter
    search_fields = ['title', 'message']
    ordering_fields = ['created_at', 'is_read', 'notification_type', 'read_at', 'title']
    ordering = ['-created_at']
    pagination_class = NotificationResultsSetPagination

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        validate_notification_filter_params(request.query_params)
        return super().list(request, *args, **kwargs)


@extend_schema(
    tags=['Notifications'],
    summary='Retrieve, Update, or Delete Notification',
    description='Retrieves, updates (e.g. mark as read), or deletes a notification.',
    responses={
        200: NotificationSerializer,
        401: OpenApiResponse(description='Authentication required'),
        404: OpenApiResponse(description='Notification not found'),
    }
)
class NotificationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update (PATCH for read status), or delete a notification owned by the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return NotificationUpdateSerializer
        return NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        read_serializer = NotificationSerializer(instance, context={'request': request})
        return response.Response(read_serializer.data, status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        n_id = instance.id
        super().perform_destroy(instance)
        AuditLogService.log_delete(self.request.user, 'Notification', n_id, request=self.request)


@extend_schema(
    tags=['Notifications'],
    summary='Mark All Notifications as Read',
    description='Marks all unread notifications for the current authenticated user as read.',
    request=None,
    responses={
        200: inline_serializer(
            name='MarkAllReadResponse',
            fields={
                'message': serializers.CharField(default='All notifications marked as read.'),
                'updated_count': serializers.IntegerField(),
            }
        ),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class NotificationMarkAllReadView(APIView):
    """
    Mark all unread notifications as read for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        count = NotificationService.mark_all_as_read(request.user)
        AuditLogService.log_update(request.user, 'Notification', resource_id='all', metadata={'action': 'mark_all_read', 'count': count}, request=request)
        return response.Response({
            'message': 'All notifications marked as read.',
            'updated_count': count
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Audit Logs'],
    summary='List Audit Logs',
    description='Retrieves security and activity audit logs for actions performed by the user.',
    responses={
        200: AuditLogSerializer(many=True),
        400: OpenApiResponse(description='Invalid filter parameters'),
        401: OpenApiResponse(description='Authentication required'),
    }
)
class AuditLogListView(generics.ListAPIView):
    """
    GET /api/audit-logs/
    List audit logs for the authenticated user with filtering, search, pagination, and ordering.
    """
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AuditLogFilter
    search_fields = ['action', 'resource_type', 'resource_id']
    ordering_fields = ['timestamp', 'action', 'resource_type']
    ordering = ['-timestamp']
    pagination_class = AuditLogResultsSetPagination

    def get_queryset(self):
        return AuditLog.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        validate_audit_filter_params(request.query_params)
        return super().list(request, *args, **kwargs)


@extend_schema(
    tags=['Audit Logs'],
    summary='Retrieve Audit Log Entry',
    description='Retrieves a specific audit log entry by ID.',
    responses={
        200: AuditLogSerializer,
        401: OpenApiResponse(description='Authentication required'),
        404: OpenApiResponse(description='Audit log entry not found'),
    }
)
class AuditLogDetailView(generics.RetrieveAPIView):
    """
    GET /api/audit-logs/<id>/
    Retrieve a specific audit log entry owned by the authenticated user.
    """
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return AuditLog.objects.filter(user=self.request.user)







