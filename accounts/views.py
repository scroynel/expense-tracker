from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.contrib.auth import get_user_model, authenticate, login
from .serializer import RegisterSerializer

from .throttle import LoginThrottling


User = get_user_model()


class LoginView(APIView):
    throttle_classes = [LoginThrottling,]


    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, email=email, password=password)

        if not user:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        
        login(request, user)
        return Response({'detail': 'Logged In'}, status=status.HTTP_200_OK)
        


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    # throttle_classes = [AnonRateThrottle, ]
    throttle_scope = 'login'
    



