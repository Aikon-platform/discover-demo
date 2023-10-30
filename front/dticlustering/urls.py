from django.urls import path
from .views import *

app_name = 'dticlustering'

urlpatterns = [
    path('', DTIClusteringStart.as_view(), name='start'),
    path('<uuid:pk>', DTIClusteringStatus.as_view(), name='status'),
    path('<uuid:pk>/progress', DTIClusteringProgress.as_view(), name='progress'),
    path('<uuid:pk>/cancel', DTIClusteringCancel.as_view(), name='cancel'),
    path('<uuid:pk>/watch', DTIClusteringWatcher.as_view(), name='notify'),
    path('<uuid:pk>/restart', DTIClusteringStartFrom.as_view(), name='restart'),
    path('<uuid:from_pk>/saved/create', SavedClusteringFromDTI.as_view(), name='saved_create'),
    path('<uuid:from_pk>/saved/<uuid:pk>', SavedClusteringEdit.as_view(), name='saved'),
    path('list', DTIClusteringList.as_view(), name='list'),
]
