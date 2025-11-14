# authentication.py
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from django.utils.translation import gettext_lazy as _
from .models import AuthToken


class DRFUserWrapper:
    """
    Wraps a User or Client instance to be DRF-compatible.
    """
    def __init__(self, obj):
        self._obj = obj

    @property
    def is_authenticated(self):
        return True  # DRF expects this property

    def __getattr__(self, attr):
        # Forward all other attribute access to the original object
        return getattr(self._obj, attr)


class CustomTokenAuthentication(BaseAuthentication):
    """
    Token-based authentication using AuthToken model.
    Supports both User and Client tokens.
    Works with never-expiring tokens.
    """
    keyword = 'Token'

    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            # No header sent, let DRF handle permissions
            return None

        if not auth_header.startswith(self.keyword):
            raise exceptions.AuthenticationFailed(
                _('Invalid token header prefix. Expected "Token".')
            )

        try:
            token = auth_header.split()[1]
        except IndexError:
            raise exceptions.AuthenticationFailed(
                _('Invalid token header. No credentials provided.')
            )

        try:
            token_obj = AuthToken.objects.get(token=token)
        except AuthToken.DoesNotExist:
            raise exceptions.AuthenticationFailed(_('Invalid token.'))

        # No expiry check needed — token is permanent

        # Wrap both User and Client for DRF compatibility
        if token_obj.user:
            return (DRFUserWrapper(token_obj.user), token_obj)
        elif token_obj.client:
            return (DRFUserWrapper(token_obj.client), token_obj)
        else:
            raise exceptions.AuthenticationFailed(_('Token has no valid owner.'))

    def authenticate_header(self, request):
        return self.keyword
