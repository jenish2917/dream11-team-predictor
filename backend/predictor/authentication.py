"""
Authentication views for the predictor app
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError

class RegisterView(APIView):
    """
    API view for user registration
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handle user registration
        """
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')

        print(f"Registration attempt: username='{username}', email_raw='{email}'") # Log raw email
        
        if not username or not password:
            return Response({'error': 'Username and password are required'}, status=status.HTTP_400_BAD_REQUEST)
            
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
        
        user_email = email.strip() if email and email.strip() else None
        print(f"Processed email for create_user: user_email='{user_email}'") # Log processed email

        try:
            user = User.objects.create_user(username=username, email=user_email, password=password)
        except DjangoValidationError as e:
            print(f"DjangoValidationError during create_user: {e.message_dict}") # Log specific validation error
            # Check if the error is specifically about the email field and if user_email was intended to be None
            if 'email' in e.message_dict and user_email is None:
                print(f"Validation failed for email despite user_email being None. Raw email was: '{email}'")
            return Response({'error': e.message_dict}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Generic exception during create_user: {type(e).__name__} - {e}") # Log other errors
            return Response({'error': 'Failed to create user account (server error).'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'username': user.username,
                'email': user.email
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    API view for user login
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Handle user login
        """
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({'error': 'Username and password are required'}, status=status.HTTP_400_BAD_REQUEST)
            
        user = authenticate(username=username, password=password)
        
        if not user:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
            
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'username': user.username,
                'email': user.email
            }
        })
