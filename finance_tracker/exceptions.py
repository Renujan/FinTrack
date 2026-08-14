from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom DRF exception handler to provide consistent, clean error responses
    for 400, 401, 403, 404, and 500 HTTP errors without exposing raw tracebacks.
    """
    response = exception_handler(exc, context)

    if response is not None:
        if isinstance(response.data, dict):
            if 'detail' not in response.data and 'error' not in response.data:
                # Retain original field errors for compatibility with serializers
                pass
        elif isinstance(response.data, list):
            first_msg = response.data[0] if len(response.data) > 0 else "Invalid input."
            response.data = {
                'detail': str(first_msg),
                'errors': response.data
            }
        return response

    # Handle unhandled exceptions (500 Server Error)
    logger.error(f"Unhandled exception in API request: {exc}", exc_info=True)
    return Response(
        {
            'detail': 'An internal server error occurred. Please try again later.',
            'error_code': 'internal_server_error'
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
