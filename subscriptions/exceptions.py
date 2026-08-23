from rest_framework.exceptions import APIException
from rest_framework import status


class PlanLimitReachedException(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = 'PLAN_LIMIT_REACHED'

    def __init__(self, limit_type, current_usage, max_allowed, detail=None):
        if detail is None:
            detail = f"Plan limit reached for {limit_type}. Current usage: {current_usage}, Maximum allowed: {max_allowed}."
        
        self.detail = {
            'detail': detail,
            'error_code': 'PLAN_LIMIT_REACHED',
            'limit_type': limit_type,
            'current_usage': current_usage,
            'max_allowed': max_allowed,
            'upgrade_suggestion': 'Please upgrade your subscription plan to increase your resource limits.'
        }
