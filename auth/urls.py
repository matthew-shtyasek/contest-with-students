from django.urls import path
from rest_framework.authtoken.views import ObtainAuthToken

from auth.serializers import AuthTokenSerializer
from auth.views import RegistrationAPIView, LogoutAPIView

app_name = 'custom_auth'


urlpatterns = [
    path('authorization', ObtainAuthToken.as_view(serializer_class=AuthTokenSerializer)),
    path('registration', RegistrationAPIView.as_view()),
    path('logout', LogoutAPIView.as_view()),
]
