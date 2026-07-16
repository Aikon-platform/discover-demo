from django import forms

from .models import Paleography
from tasking.forms import AbstractTaskOnDatasetForm


class PaleographyForm(AbstractTaskOnDatasetForm):
    """
    Formulaire réduit à la SEULE partie dataset-upload (décision réunion #9) :
    on n'ajoute aucun champ de paramètre (pas de "model", pas de post-traitement),
    contrairement à `RegionsForm`. La création du dataset est gérée par la base
    (`_populate_dataset` -> `Dataset.objects.create`).
    """

    class Meta(AbstractTaskOnDatasetForm.Meta):
        model = Paleography
        fields = AbstractTaskOnDatasetForm.Meta.fields  # upload seulement

    # [À CONFIRMER avec Paul + voir AbstractDatasetForm] Restreindre le format à Zip
    # uniquement (décision #4 : "dans les types il y aura que Zip"). Le champ `format`
    # vient de AbstractDatasetForm ; le filtrer en __init__ dès qu'on a vu ses choices.
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.fields["format"].choices = [
    #         c for c in self.fields["format"].choices if c[0] == "zip"
    #     ]
