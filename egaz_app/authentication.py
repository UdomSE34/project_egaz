# from rest_framework.authentication import BaseAuthentication
# from rest_framework.exceptions import AuthenticationFailed
# from .models import AuthToken

# class CustomTokenAuthentication(BaseAuthentication):
#     def authenticate(self, request):
#         auth_header = request.headers.get("Authorization")
#         if not auth_header or not auth_header.startswith("Token "):
#             return None  # no token passed

#         token_key = auth_header.split(" ")[1]

#         try:
#             token_obj = AuthToken.objects.get(token=token_key)
#         except AuthToken.DoesNotExist:
#             raise AuthenticationFailed("Invalid or expired token")

#         # kama ni user
#         if token_obj.user:
#             request.client = None
#             return (token_obj.user, token_obj)

#         # kama ni client
#         if token_obj.client:
#             request.client = token_obj.client
#             return (token_obj.client, token_obj)

#         raise AuthenticationFailed("Token not linked to any account")
