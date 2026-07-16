from .forms import PaleographyForm
from .models import Paleography
from tasking.views import task_view_set


# Génère les vues Start / Status / Progress / Cancel / Delete / List ... (cf. regions)
@task_view_set
class PaleographyMixin:
    """
    Mixin pour les vues Paleography.
    """

    model = Paleography
    form_class = PaleographyForm
    task_name = "Paleography"
    app_name = "paleography"
    # NOTE: task_data="dataset" pour utiliser le template de formulaire dataset
    task_data = "dataset"

# [ÉTAPE SUIVANTE] La page de visu (images à gauche / transcriptions à droite)
# se fera en surchargeant Status, sur le modèle de RegionsStatus.
