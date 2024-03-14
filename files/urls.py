from django.urls import path

from files.views import FileUploadAPIView, FileRetrieveAPIView, FilePermissionAPIView, FilesRetrieveAPIView

app_name = 'files'

urlpatterns = [
    path('files', FileUploadAPIView.as_view()),
    path('files/disk', FilesRetrieveAPIView.as_view()),
    path('files/<str:file_id>', FileRetrieveAPIView.as_view()),
    path('files/<str:file_id>/accesses', FilePermissionAPIView.as_view()),
]
