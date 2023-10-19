from celery import shared_task

from .models import DTIClustering

@shared_task
def collect_results(dticlustering_id):
    dticlustering = DTIClustering.objects.get(id=dticlustering_id)
    
    # TODO
    # download the results from the API

    # extract the results from the .zip file

    # mark clustering as ready