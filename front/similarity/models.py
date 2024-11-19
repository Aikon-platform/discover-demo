from django.contrib.auth import get_user_model
from django.db import models
import uuid

from tasking.models import AbstractAPITaskOnDataset

User = get_user_model()


class Similarity(AbstractAPITaskOnDataset("similarity")):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
