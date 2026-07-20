from django import forms

from .models import Paleography
from tasking.forms import AbstractTaskOnDatasetForm


class PaleographyForm(AbstractTaskOnDatasetForm):
    """
    Formulaire réduit à la SEULE partie dataset-upload (décision réunion #9),
    restreint au format Zip (décision #4), avec les transcriptions attendues
    par défaut (le module paléographie travaille sur des datasets transcrits).
    """

    class Meta(AbstractTaskOnDatasetForm.Meta):
        model = Paleography
        fields = AbstractTaskOnDatasetForm.Meta.fields  # upload seulement

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Décision #4 : paléographie n'accepte que le Zip.
        # `format` est un ChoiceField dont les choix sont posés par
        # AbstractDatasetForm.__init__ ; on les restreint à la seule entrée "zip".
        self.fields["format"].choices = [
            choice for choice in self.fields["format"].choices if choice[0] == "zip"
        ]
        self.fields["format"].initial = "zip"

        # Checkbox "has transcriptions" cochée par défaut dans ce module
        # (un dataset paléographie est censé porter ses transcriptions).
        if "has_transcriptions" in self.fields:
            self.fields["has_transcriptions"].initial = True
