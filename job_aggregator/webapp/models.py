import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


from datetime import timedelta


class EmailVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    verified = models.BooleanField(default=False)

    @property
    def token_expired(self):
        expiration_duration = timedelta(
            minutes=30
        )  # Use timedelta to define the expiration duration
        return (
            self.created_at < timezone.now() - expiration_duration
        )  # Correct the comparison
