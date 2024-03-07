from django.db import models

from auth.models import User


class File(models.Model):
    name = models.CharField(max_length=128)
    file_id = models.CharField(max_length=10)
    owner = models.ForeignKey(User, models.DO_NOTHING)
    coowners = models.ManyToManyField(User,
                                      related_name='files',
                                      through='FilePermission',
                                      through_fields=('file', 'user'))

    class Meta:
        managed = False
        db_table = 'file'


class FilePermission(models.Model):
    user = models.ForeignKey(User, models.DO_NOTHING)
    file = models.ForeignKey(File, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'file_permission'

