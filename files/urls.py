from django.urls import path

from files.views import FileUploadAPIView

app_name = 'files'

urlpatterns = [
    path('files', FileUploadAPIView.as_view()),
]
