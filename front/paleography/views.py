from pathlib import PurePosixPath

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


class PaleographyStatus(PaleographyMixin.Status):
    """
    Page de résultat : image de ligne à gauche, transcription à droite (décision #8).
    On aligne chaque image sur sa transcription par le radical (chemin relatif sans
    extension), car `Document._list_img_dir` pose `image.src = <dossier>/<nom.ext>`
    et nos clés de transcription sont `<dossier>/<nom>` (sans extension).
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = self.object

        transcriptions = task.transcriptions or {}
        rows = []

        if task.dataset:
            # Rapatrie les images depuis l'API + extraction locale (idempotent).
            # Sans cet appel, doc.images renvoie [] et la page affiche "(0)".
            try:
                task.dataset.get_images()
            except Exception as e:
                print(f"[paleography] get_images a echoue: {e}")

            for document in task.dataset.documents:
                for image in document.images:
                    # radical = identifiant sans extension, en posix (ex: "manuscrit_A/ligne_001")
                    # NB: on utilise image.id (chemin relatif), image.src pouvant etre None
                    rel = image.id or image.src or ""
                    stem_key = str(PurePosixPath(str(rel)).with_suffix(""))
                    text = transcriptions.get(stem_key)
                    if text is None:
                        continue  # image sans transcription -> ignorée (décision #5)
                    rows.append({"image": image, "text": text, "key": stem_key})

        # tri stable par clé pour un affichage déterministe
        rows.sort(key=lambda r: r["key"])
        context["paleo_rows"] = rows
        return context
