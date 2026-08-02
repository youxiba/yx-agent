import logging
from rest_framework.views import exception_handler
from rest_framework import status as http_status
from rest_framework.exceptions import APIException, ValidationError
from common.result import Result

logger = logging.getLogger("yx-agent")


class AppApiException(Exception):
    """业务异常：code 为业务码，message 为给用户的提示"""
    def __init__(self, message="业务错误", code=500, status=None):
        self.message, self.code, self.status = message, code, status or 200
        super().__init__(message)


class PermissionDenied(AppApiException):
    def __init__(self, message="无权限"):
        super().__init__(message=message, code=403, status=http_status.HTTP_403_FORBIDDEN)


def handle_exception(exc, context):
    if isinstance(exc, AppApiException):
        return Result.error(message=exc.message, code=exc.code, status=exc.status)
    if isinstance(exc, ValidationError):
        detail = exc.detail
        first = detail if isinstance(detail, str) else next(iter(detail.values()))[0]
        return Result.error(message=str(first), code=400, status=http_status.HTTP_400_BAD_REQUEST)
    resp = exception_handler(exc, context)          # 兜底给 DRF 默认
    if resp is not None:
        return resp
    logger.exception("unhandled error")
    return Result.error(message="服务器内部错误", code=500, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)

