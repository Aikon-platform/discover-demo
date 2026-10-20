from django.db.models import Q
from .models import Indexing, Query, Index
from tasking.forms import AbstractTaskOnCropsForm
from django import forms
from .widgets import IndexRadioSelect


class IndexingForm(AbstractTaskOnCropsForm):
    """Form for creating indexing tasks."""

    class Meta(AbstractTaskOnCropsForm.Meta):
        model = Indexing
        fields = AbstractTaskOnCropsForm.Meta.fields + ("feat_net",)

    feat_net = forms.ChoiceField(
        label="Feature Extraction Model",
        help_text="Select the model to use for feature extraction",
        widget=forms.Select(attrs={"extra-class": "preprocessing-field"}),
    )

    use_transpositions = forms.BooleanField(
        required=False,
        initial=False,
        label="Use Transpositions",
        help_text="Include transposed images in similarity computation",
        widget=forms.CheckboxInput(attrs={"extra-class": "preprocessing-field"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["feat_net"].choices = Indexing.get_available_models()

    def save(self, commit=True):
        instance = super().save(commit=False)

        parameters = {
            "feat_net": self.cleaned_data["feat_net"],
            "transpositions": (
                ["none"]
                if not self.cleaned_data["use_transpositions"]
                else ["none", "hflip"]
            ),
        }
        instance.parameters = parameters

        if commit:
            instance.save()

        return instance


class IndexEditForm(forms.ModelForm):
    class Meta:
        model = Index
        fields = ("name", "public", "description")
        help_texts = {
            "name": "Public name of the index",
            "public": "Make the searchable by all users",
            "description": "Description of the index",
        }


class QueryForm(AbstractTaskOnCropsForm):
    """Form for creating query tasks."""

    class Meta(AbstractTaskOnCropsForm.Meta):
        model = Query
        fields = AbstractTaskOnCropsForm.Meta.fields + ("target_index",)

    target_index = forms.ModelChoiceField(
        queryset=Index.objects.filter(public=True),
        label="Index",
        help_text="Select the index to query",
        widget=IndexRadioSelect(),
    )

    use_transpositions = forms.BooleanField(
        required=False,
        initial=True,
        label="Use Transpositions",
        help_text="Include transposed images in similarity computation",
        widget=forms.CheckboxInput(attrs={"extra-class": "preprocessing-field"}),
    )

    def __init__(self, *args, **kwargs):
        selected_index = kwargs.pop("target_index", None)
        super().__init__(*args, **kwargs)
        self.fields["target_index"].queryset = Index.available_indexes(self._user)
        self.fields["target_index"].initial = selected_index

    def save(self, commit=True):
        instance = super().save(commit=False)

        parameters = {
            "transpositions": (
                ["none"]
                if not self.cleaned_data["use_transpositions"]
                else ["none", "rot90", "rot180", "rot270"]
            )
        }
        instance.parameters = parameters

        if commit:
            instance.save()

        return instance
