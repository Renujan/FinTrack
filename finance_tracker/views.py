from django.db import connection
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health_check(request):
    """
    Backend health-check endpoint.
    Verifies operational status and basic database connectivity.
    """
    db_ok = True
    try:
        connection.ensure_connection()
    except Exception:
        db_ok = False

    if db_ok:
        return Response(
            {
                "status": "healthy",
                "database": "connected"
            },
            status=status.HTTP_200_OK
        )
    return Response(
        {
            "status": "unhealthy",
            "database": "disconnected"
        },
        status=status.HTTP_503_SERVICE_UNAVAILABLE
    )
