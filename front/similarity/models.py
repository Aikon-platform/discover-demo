from django.contrib.auth import get_user_model
from django.db import models
import uuid

User = get_user_model()


class Similarity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class SavedSimilarity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
