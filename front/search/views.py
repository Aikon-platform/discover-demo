from .models import Index, Query, Indexing
from tasking.views import task_view_set
from django.views.generic import TemplateView, UpdateView
from django.urls import reverse
from typing import Any

from .forms import IndexingForm, QueryForm, IndexEditForm


@task_view_set
class IndexingMixin:
    """
    Mixin for Indexing views
    """

    model = Indexing
    form_class = IndexingForm
    task_name = "Dataset Indexing"
    app_name = "search"
    task_data = "dataset"


class IndexingStatusView(IndexingMixin.Status):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["editable"] = (
            hasattr(self.object, "index")
            and self.object.index.owner == self.request.user
        ) or self.request.user.is_superuser
        return context


class IndexEditView(UpdateView):
    model = Index
    form_class = IndexEditForm
    template_name = "search/index_edit.html"

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Index.objects.none()
        if self.request.user.is_superuser:
            return Index.objects.all()
        return Index.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["url_prefix"] = "search:indexing_"
        return context

    def get_success_url(self):
        if self.object.from_task:
            return self.object.from_task.get_absolute_url()
        return reverse("search:indexing_list")


@task_view_set
class QueryMixin:
    """
    Mixin for Search views
    """

    model = Query
    form_class = QueryForm
    task_name = "Search in index"
    app_name = "search"
    task_data = "dataset"


class QueryStartMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if "index" in self.request.GET:
            kwargs["target_index"] = self.request.GET["index"]
        return kwargs

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["dataset_label"] = "Query images"
        return context


class QueryStartView(QueryStartMixin, QueryMixin.Start):
    pass


class QueryStartFromView(QueryStartMixin, QueryMixin.StartFrom):
    pass


class SearchHomeView(TemplateView):
    template_name = "search/home.html"
