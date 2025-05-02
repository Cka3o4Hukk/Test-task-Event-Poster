from rest_framework.response import Response


class ErrorHandlingMixin:
    def create_error_response(self, detail, status_code):
        return Response(
            {"detail": detail},
            status=status_code)
