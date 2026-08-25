"""
Standardized API Error Handler & Exception Sanitizer for SaaS Finance Tracker.
Covers 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found,
409 Conflict, 429 Too Many Requests, and 500 Internal Server Errors.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)



def sanitize_error_data(data):
    """
    Recursively sanitize response data to ensure sensitive credential details
    or internal filesystem secrets are not exposed in error bodies.
    """
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            key_lower = str(key).lower()
            if any(s in key_lower for s in ['secret_key', 'db_password', 'private_key']):
                cleaned[key] = ["Redacted for security."]
            else:
                cleaned[key] = sanitize_error_data(value)
        return cleaned
    elif isinstance(data, list):
        return [sanitize_error_data(item) for item in data]
    return data


def custom_exception_handler(exc, context):
    """
    Custom DRF exception handler providing consistent, sanitized error responses
    for 400, 401, 403, 404, 409, 429, and 500 HTTP errors without exposing raw tracebacks
    or internal system paths.
    """
    response = exception_handler(exc, context)

    if response is not None:
        response.data = sanitize_error_data(response.data)

        if isinstance(response.data, dict):
            # Ensure top-level detail field for generic dictionary responses if missing
            if 'detail' not in response.data and 'error' not in response.data:
                first_key = next(iter(response.data)) if response.data else None
                if first_key:
                    first_val = response.data[first_key]
                    if isinstance(first_val, list) and first_val:
                        response.data['detail'] = f"{first_key}: {first_val[0]}"
                    elif isinstance(first_val, str):
                        response.data['detail'] = f"{first_key}: {first_val}"
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
