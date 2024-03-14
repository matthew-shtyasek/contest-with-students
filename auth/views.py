from django.shortcuts import render
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.generics import CreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auth.authentications import BearerAuthentication
from auth.models import User
from auth.serializers import UserSerializer, AuthTokenSerializer


class RegistrationAPIView(CreateAPIView):
    model = User
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token = Token.objects.create(user=user)
            return Response({'success': True, 'message': 'Success', 'token': token.key}, status=status.HTTP_200_OK)
        return Response({'success': False, 'message': serializer.errors}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


class LogoutAPIView(APIView):
    # permission_classes = [IsAuthenticated]
    authentication_classes = [BearerAuthentication]

    def get(self, request, *args, **kwargs):
        user = request.user

        if not user.is_authenticated:
            return Response({'message': 'Login failed'}, status=status.HTTP_403_FORBIDDEN)

        token = get_object_or_404(Token, user=user)
        token.delete()

        return Response({'success': True, 'message': 'Logout'}, status=status.HTTP_200_OK)
