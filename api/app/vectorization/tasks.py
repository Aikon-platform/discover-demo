import dramatiq
from typing import Optional

from .const import VEC_QUEUE
from .lib.vectorization import LoggedComputeVectorization
from ..shared.utils.logging import notifying, TLogger, LoggerHelper


# @notifying TODO implement results return with notifying
@dramatiq.actor(time_limit=1000 * 60 * 60, max_retries=0, queue_name=VEC_QUEUE)
def compute_vectorization(
    experiment_id: str,
    dataset: dict,
    notify_url: Optional[str] = None,
    logger: TLogger = LoggerHelper,
    doc_id = str,
    model = str
):
    """
    Run vecto task on list of URL

    Parameters:
    - experiment_id: the ID of the vecto task
    - dataset: dictionary containing the documents to be vectorized
    - notify_url: the URL to be called when the task is finished
    - logger: a logger object
    - doc_id : the id of the annotated witness

    E.g. of dataset dict
    {
    "wit4_man19_0023_260,1335,1072,1114": "http://localhost:8182/iiif/2/wit4_man19_0023.jpg/260,1335,1072,1114/full/0/default.jpg", 
    "wit4_man19_0025_244,1462,768,779": "http://localhost:8182/iiif/2/wit4_man19_0025.jpg/244,1462,768,779/full/0/default.jpg", 
    "wit4_man19_0030_15,1523,623,652": "http://localhost:8182/iiif/2/wit4_man19_0030.jpg/15,1523,623,652/full/0/default.jpg"
    }
    """

    vectorization_task = LoggedComputeVectorization(
        logger, dataset=dataset, notify_url=notify_url, doc_id=doc_id
    )
    vectorization_task.run_task()