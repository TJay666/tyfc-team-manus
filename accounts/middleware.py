from django.utils.deprecation import MiddlewareMixin
from django.middleware.csrf import get_token

class CsrfViewMiddleware(MiddlewareMixin):
    """
    自定義中間件，確保每個響應都包含CSRF令牌
    """
    def process_response(self, request, response):
        # 確保CSRF令牌被設置
        get_token(request)
        return response

