import dramatiq
import requests
from zipfile import ZipFile
import traceback

from .models import DTIClustering

"""
All dramatiq tasks related to the DTI clustering
"""


@dramatiq.actor
def collect_results(experiment_id: str, result_url: str):
    """
    Download the results from the API and save them to the dticlustering.results_path
    """
    try:
        dticlustering = DTIClustering.objects.get(id=experiment_id)
    except Exception as e:
        print(
            f"[dticlustering.collect_results] Unknown DTIClustering: experiment_id doesn't match any record {e}"
        )
        return

    try:
        # download the results from the API
        res = requests.get(result_url, stream=True)
        res.raise_for_status()
        dticlustering.result_full_path.mkdir(parents=True, exist_ok=True)
        zip_result_file = dticlustering.result_full_path / "results.zip"

        with open(zip_result_file, "wb") as f:
            for chunk in res.iter_content(chunk_size=8192):
                f.write(chunk)

        # unzip the results
        with ZipFile(zip_result_file, "r") as zip_obj:
            zip_obj.extractall(dticlustering.result_full_path)

        # create a summary.zip file, with cherry-picked content
        summary_zip = dticlustering.result_full_path / "summary.zip"
        cherrypick = [
            "*.csv",
            "clusters.html",
            "clusters/**/*_raw.*",
            "backgrounds/*",
            "masked_prototypes/*",
            "prototypes/*",
        ]

        with ZipFile(summary_zip, "w") as zipObj:
            for cp in cherrypick:
                for f in dticlustering.result_full_path.glob(cp):
                    zipObj.write(f, f.relative_to(dticlustering.result_full_path))

        # mark the dticlustering as finished
        dticlustering.terminate_task()
    except Exception:
        dticlustering.terminate_task(status="ERROR", error=traceback.format_exc())
