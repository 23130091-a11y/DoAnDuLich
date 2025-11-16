from django.shortcuts import render, get_object_or_404
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import UserSerializer

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken


# Create your views here.
class RegisterView(APIView) :
    def post (self, request) :
        serializer = UserSerializer(data = request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response = Response()
        response.data = serializer.data
        return response

class LoginView(APIView) :
    def post(self, request):
        email = request.data.get("email", None)
        user = get_object_or_404(User, email=email)

        password = request.data.get("password", None)
        is_check = user.check_password(password)
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })
        # if not is_check :
        #     raise AuthenticationFailed("Authentication Failed")
        #
        # if user is not None:
        #     # tạo token hoặc lấy token hiện tại
        #     token, created = Token.objects.get_or_create(user=user)
        #
        #     return Response({
        #         "message": "Login successful",
        #         "email": user.email,
        #         "token": token.key
        #     }, status=status.HTTP_200_OK)
        # else:
        #     return Response(
        #         {"error": "Invalid email or password"},
        #         status=status.HTTP_401_UNAUTHORIZED
        #     )