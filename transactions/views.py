from django.db.models import ProtectedError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, filters, status, response
from .filters import TransactionFilter, validate_filter_params
from .models import Category, Transaction
from .pagination import StandardResultsSetPagination
from .permissions import IsOwner
from .serializers import CategorySerializer, TransactionSerializer


class CategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user).order_by('name')

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
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TransactionFilter
    search_fields = ['description', 'category__name']
    ordering_fields = ['date', 'amount', 'created_at']
    ordering = ['-date', '-created_at']
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    def filter_queryset(self, queryset):
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
        return Transaction.objects.filter(user=self.request.user)
