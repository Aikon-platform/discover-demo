from .models import WatermarkProcessing
from tasking.forms import AbstractTaskOnImageForm


class WatermarkProcessingForm(AbstractTaskOnImageForm):
    class Meta:
        model = WatermarkProcessing
        fields = ("image", "detect", "compare_to")
