from django import forms

from datasets.models import ZippedDataset, path_datasets

from .models import DTIClustering

class DTIClusteringForm(forms.ModelForm):
    dataset_zip = forms.FileField(label='Dataset', help_text='A .zip file containing the dataset to be clustered')

    class Meta:
        model = DTIClustering
        fields = ('dataset_zip', 'notify_email')

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.dataset = ZippedDataset.objects.create(zip_file=self.cleaned_data['dataset_zip'])
        if commit:
            instance.save()
        return instance