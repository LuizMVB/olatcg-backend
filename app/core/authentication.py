from datetime import timedelta
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authtoken.models import Token
from django.utils import timezone
from .constants import AUTH_TOKEN_LIFETIME

class ExpiringTokenAuthentication(TokenAuthentication):
    token_lifetime = timedelta(minutes=AUTH_TOKEN_LIFETIME)

    def authenticate_credentials(self, key):
        try:
            token = Token.objects.select_related('user').get(key=key)
        except Token.DoesNotExist:
            raise AuthenticationFailed('Invalid token.')

        if not token.user.is_active:
            raise AuthenticationFailed('Inactive or deleted user.')

        if timezone.now() - token.created > self.token_lifetime:
            token.delete()
            raise AuthenticationFailed('Expired token. Try to make login again.')

        return (token.user, token)