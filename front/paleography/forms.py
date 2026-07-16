from django import forms

from .models import Paleography
from tasking.forms import AbstractTaskOnDatasetForm


class PaleographyForm(AbstractTaskOnDatasetForm):
    """
    Formulaire réduit à la SEULE partie dataset-upload (décision réunion #9),
    restreint au format Zip (décision #4).
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
        # valeur par défaut = zip (un seul choix, autant le pré-sélectionner)
        self.fields["format"].initial = "zip"
