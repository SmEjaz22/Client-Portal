# from django.contrib.auth.models import User

# # Creating a custom authentication backend is as simple as writing a Python class that implements both methods. Let's create an authentication backend to let users authenticate in your site using their email address instead of their username.
# class EmailAuthBackend:
#     """
#     Authenticate using an e-mail address.
#     """
#     def authenticate(self, request, username=None, password=None):
#         try:
#             user = User.objects.get(email=username)
#             if user.check_password(password):
#                 return user
#             return None
#         except User.DoesNotExist:
#             return None
#     def get_user(self, user_id):
#         try:    
#             return User.objects.get(pk=user_id)
#         except User.DoesNotExist:
#             return None
        
        
        
        
from django.contrib.auth.models import User
from django.db.models import Q

class EmailOrUsernameAuthBackend:
    """
    Authenticate using either username or email.
    """
    def authenticate(self, request, username=None, password=None):
        try:
            user = User.objects.get(Q(username=username) | Q(email=username))
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
