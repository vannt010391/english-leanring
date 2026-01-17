from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('learner', 'Learner'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='learner')

    class Meta:
        db_table = 'users'

    def is_admin(self):
        return self.role == 'admin'

    def is_learner(self):
        return self.role == 'learner'
