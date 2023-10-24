from django.urls import path
from .views import *

app_name = 'dticlustering'

urlpatterns = [
    path('', DTIClusteringStart.as_view(), name='start'),
    path('<uuid:pk>', DTIClusteringStatus.as_view(), name='status'),
    path('<uuid:pk>/progress', DTIClusteringProgress.as_view(), name='progress'),
    path('<uuid:pk>/cancel', DTIClusteringCancel.as_view(), name='cancel'),
    path('<uuid:pk>/return', DTIClusteringCallback.as_view(), name='callback'),
    path('<uuid:pk>/restart', DTIClusteringStartFrom.as_view(), name='restart'),
    path('list', DTIClusteringList.as_view(), name='list'),
]
