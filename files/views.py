import os
import string
import random

from django.conf import settings
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auth.authentications import BearerAuthentication
from auth.models import User
from files.models import File, FilePermission


class FileUploadAPIView(APIView):
    model = File
    # permission_classes = [IsAuthenticated]
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
        if not request.user.is_authenticated:
            return Response({'message': 'Login failed'}, status=status.HTTP_403_FORBIDDEN)

        files = request.FILES.getlist('files')

        folder_path = settings.MEDIA_ROOT / request.user.email

        if not os.path.exists(folder_path):
            os.mkdir(folder_path)

        messages = []
        for i, file in enumerate(files):
            if not self.validate_extension(file.name):
                messages.append({'success': False,
                                 'message': {'extension': 'Extension not allowed'},
                                 'name': file.name})
            if not self.validate_size(file):
                if len(messages) == i:
                    messages.append({'success': False,
                                     'message': {'size': 'Size is too large'},
                                     'name': file.name})
                else:
                    messages[-1]['message']['size'] = 'Size is too large'

            if len(messages) != i:
                continue

            filename = self.filename_correction(file.name, request.user)
            file_id = self.generate_fileid()

            with open(folder_path / filename, 'wb') as f:
                f.write(file.read())

            logical_file = self.model(name=filename, file_id=file_id, owner=request.user)
            logical_file.save()

            messages.append({'success': True,
                             'message': 'Success',
                             'name': logical_file.name,
                             'url': f'http://127.0.0.1:8000/files/{logical_file.file_id}',
                             'file_id': logical_file.file_id})
        return Response(messages, status=status.HTTP_200_OK)


class FileRetrieveAPIView(APIView):
    authentication_classes = [BearerAuthentication]
    model = File

    def get(self, request, file_id):
        file_logic = get_object_or_404(self.model, file_id=file_id)

        if not request.user.is_authenticated:
            return Response({'message': 'Login failed'}, status=status.HTTP_403_FORBIDDEN)
        if request.user != file_logic.owner and request.user not in file_logic.coowners.all():
            return Response({'message': 'Forbidden for you'}, status=status.HTTP_403_FORBIDDEN)

        file_path = settings.MEDIA_ROOT / file_logic.owner.email / file_logic.name
        if not file_path.exists():
            return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        file = open(file_path, 'rb')

        response = FileResponse(file)
        response['Content-Type'] = 'application/octet-stream'
        return response


class FilesRetrieveAPIView(APIView):
    authentication_classes = [BearerAuthentication]
    model = File

    def get(self, request):
        if not request.user.is_authenticated:
            return Response({'message': 'Login failed'}, status=status.HTTP_403_FORBIDDEN)

        files = File.objects.filter(owner=request.user)

        return Response([{'file_id': file.file_id,
                          'name': file.name,
                          'url': f'http://127.0.0.1:8000/files/{file.file_id}',
                          'accesses': [{'fullname': request.user.fullname,
                                        'email': request.user.email,
                                        'type': 'author'}]
                                      + [{'fullname': coowner.fullname,
                                          'email': coowner.email,
                                          'type': 'co-author'}
                                         for coowner in file.coowners.all()]}
                         for file in files], status=status.HTTP_200_OK)


class FilePermissionAPIView(APIView):
    authentication_classes = [BearerAuthentication]

    def delete(self, request, file_id):
        file_logic = get_object_or_404(File, file_id=file_id)

        if not request.user.is_authenticated:
            return Response({'message': 'Login failed'}, status=status.HTTP_403_FORBIDDEN)
        if file_logic.owner != request.user:
            return Response({'message': 'Forbidden for you'}, status=status.HTTP_403_FORBIDDEN)

        coowner_email = request.data.get('email')
        coowner = get_object_or_404(User, email=coowner_email)

        if coowner not in file_logic.coowners.all():
            return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        file_logic.coowners.remove(coowner)

        return Response([{"fullname": request.user.fullname,
                          "email": request.user.email,
                          "type": "author"}], status=status.HTTP_200_OK)

    def post(self, request, file_id):
        file_logic = get_object_or_404(File, file_id=file_id)

        if not request.user.is_authenticated:
            return Response({'message': 'Login failed'}, status=status.HTTP_403_FORBIDDEN)
        if file_logic.owner != request.user:
            return Response({'message': 'Forbidden for you'}, status=status.HTTP_403_FORBIDDEN)

        coowner_email = request.data.get('email')
        coowner = get_object_or_404(User, email=coowner_email)

        filepermission = FilePermission(user=coowner, file=file_logic)
        filepermission.save()

        return Response([{"fullname": request.user.fullname,
                          "email": request.user.email,
                          "type": "author"},
                         {"fullname": coowner.fullname,
                          "email": coowner.email,
                          "type": "co-author"}], status=status.HTTP_200_OK)


#  user11 36d225e239406af5d7d9db0197e30e7cc013f9eb
#  admin1 f26a354fd5ec8bcc46428843c1b83fde51432da9
#  admin2 9facf5684e74b16d1a27a15554b724e368342b5d
#  admin3 016142811d4fbac0a82b9cf45b5b757a36b2cd40
