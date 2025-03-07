from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject
from rest_framework.request import Request

class JWTMiddleware(MiddlewareMixin):
    """
    Middleware qui ajoute l'utilisateur JWT au request.user pour Swagger
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_auth = JWTAuthentication()
        # Ajout de l'attribut async_mode requis par Django 5.1+
        self.async_mode = False

    def process_request(self, request):
        request.user = SimpleLazyObject(lambda: self._get_user(request))
        return None

    def _get_user(self, request):
        if hasattr(request, '_jwt_user'):
            return request._jwt_user

        drf_request = Request(request)
        user = getattr(request, 'user', None)
        
        if user and user.is_authenticated:
            return user

        try:
            authenticated = self.jwt_auth.authenticate(drf_request)
            if authenticated:
                user, _ = authenticated
                request._jwt_user = user
                return user
        except:
            pass
            
        return request.user