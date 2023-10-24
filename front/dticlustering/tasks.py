import dramatiq
import requests
from zipfile import ZipFile
import traceback

from .models import DTIClustering


@dramatiq.actor
def collect_results(dticlustering_id:str, result_url:str):
    
    try:
        dticlustering = DTIClustering.objects.get(id=dticlustering_id)
        
        # download the results from the API
        # save them to the dticlustering.results_path
        
        res = requests.get(result_url, stream=True)
        res.raise_for_status()
        dticlustering.result_full_path.mkdir(parents=True, exist_ok=True)
        zipresultfile = dticlustering.result_full_path / "results.zip"

        with open(zipresultfile, "wb") as f:
            for chunk in res.iter_content(chunk_size=8192):
                f.write(chunk)

        # unzip the results
        with ZipFile(zipresultfile, "r") as zipObj:
            zipObj.extractall(dticlustering.result_full_path)

        # mark the dticlustering as finished
        dticlustering.finish_clustering()
    except:
        dticlustering.finish_clustering(status="ERROR", error=traceback.format_exc())