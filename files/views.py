import os
import string
import random

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auth.authentications import BearerAuthentication
from auth.models import User
from files.models import File


class FileUploadAPIView(APIView):
    model = File
    permission_classes = [IsAuthenticated]
    authentication_classes = [BearerAuthentication]

    FILE_PERMITTED_EXTENSIONS = ['doc', 'pdf', 'docx', 'zip', 'jpeg', 'jpg', 'png']
    FILE_MAX_SIZE = 2 * 1024 * 1024

    def validate_extension(self, filename: str) -> bool:
        name, ext = os.path.splitext(filename)  # 'contest.txt' -> ('contest', '.txt')
        ext = ext.lstrip('.')

        return ext in self.FILE_PERMITTED_EXTENSIONS

    def validate_size(self, file) -> bool:
        return file.size <= self.FILE_MAX_SIZE

    def filename_correction(self, filename: str, user: User) -> str:
        #  folder_path = settings.MEDIA_ROOT / user.email
        files_names = self.model.objects.filter(owner=user).values_list('name', flat=True)
        files_names = set(files_names)

        name, ext = os.path.splitext(filename)
        new_filename = filename
        i = 1
        while new_filename in files_names:
            new_filename = f'{name} ({i}){ext}'
            i += 1

        return new_filename

    def generate_fileid(self) -> str:
        charset = string.ascii_letters + string.digits

        while (file_id := ''.join(random.choices(charset, k=10))) in self.model.objects.all().values_list('file_id', flat=True):
            ...

        return file_id


    def post(self, request):
        files = request.FILES.getlist('files')

        folder_path = settings.MEDIA_ROOT / request.user.email

        if not os.path.exists(folder_path):
            os.mkdir(folder_path)

        for file in files:
            if not self.validate_extension(file.name):
                continue
            if not self.validate_size(file):
                continue

            filename = self.filename_correction(file.name, request.user)
            file_id = self.generate_fileid()

            with open(folder_path / filename, 'wb') as f:
                f.write(file.read())

            logical_file = self.model(name=filename, file_id=file_id, owner=request.user)
            logical_file.save()
        return Response(status=status.HTTP_201_CREATED)
