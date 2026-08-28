from transactions.models import Transaction


class RecentTransactionsMixin:
    """
    Mixin providing recent transaction dashboard data retrieval.
    Optimized with select_related('category') and query limit bounds protection.
    """

    @classmethod
    def get_recent_transactions(cls, user, limit=5):
        """
        Retrieves user's recent transactions ordered chronologically descending (-date, -id).
        Protects against unreasonable limit parameter bounds (1 to 50, defaulting to 5).
        """
        try:
            limit_int = int(limit)
            if limit_int < 1:
                limit_int = 5
            elif limit_int > 50:
                limit_int = 50
        except (ValueError, TypeError):
            limit_int = 5

        qs = (
            Transaction.objects.filter(user=user)
            .select_related('category')
            .order_by('-date', '-id')[:limit_int]
        )

        recent = []
        for txn in qs:
            cat_info = None
            if txn.category:
                cat_info = {
                    'id': txn.category.id,
                    'name': txn.category.name,
                }

            title = txn.description if txn.description else (txn.category.name if txn.category else "Transaction")

            recent.append({
                'id': txn.id,
                'title': title,
                'description': txn.description or "",
                'amount': f"{txn.amount:.2f}",
                'transaction_type': txn.transaction_type,
                'category': cat_info,
                'category_name': txn.category.name if txn.category else "Uncategorized",
                'date': txn.date.strftime('%Y-%m-%d'),
            })

        return recent
