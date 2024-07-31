from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils.deprecation import MiddlewareMixin

class CustomExceptionMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        if isinstance(exception, Http404):
            response_data = {
                "error": "Not found."
            }
            status = 404
        elif isinstance(exception, PermissionDenied):
            response_data = {
                "error": "Permission denied."
            }
            status = 403
        else:
            response_data = {
                "error": str(exception)
            }
            status = 500

        return JsonResponse(response_data, status=status)
