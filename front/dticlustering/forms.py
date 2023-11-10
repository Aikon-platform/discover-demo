from django import forms

from datasets.models import ZippedDataset, path_datasets

from .models import DTIClustering, SavedClustering

DTI_TRANSFORM_OPTIONS = [
    ('0_identity', 'Identity'),
    ('1_color', 'Color shift'),
    ('2_affine', 'Affine deformation'),
    ('3_projective', 'Projective deformation'),
    ('4_tps', 'Thin plate spline')
]

class DTIClusteringForm(forms.ModelForm):
    dataset_zip = forms.FileField(
        label='Dataset', help_text='A .zip file containing the dataset to be clustered')

    p_n_clusters = forms.IntegerField(
        label='Number of clusters', 
        help_text='The number of clusters to be generated',
        min_value=2,
        max_value=50,
        initial=10,
        required=True)
    p_use_background = forms.BooleanField(
        label='Use background', 
        help_text='Whether to separate background/foreground (using DTI sprites) or not (using DTI clustering)',
        required=False)
    p_transforms = forms.MultipleChoiceField(
        label='Transforms', 
        help_text='The transforms to be used for clustering', 
        choices=DTI_TRANSFORM_OPTIONS,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        initial=['0_identity', '1_color'])

    class Meta:
        model = DTIClustering
        fields = ('name', 'dataset_zip', 'notify_email')

    def __init__(self, *args, **kwargs):
        self.__dataset = kwargs.pop('dataset', None)

        super().__init__(*args, **kwargs)

        if self.__dataset:
            self.fields.pop('dataset_zip')

    def save(self, commit=True):
        instance = super().save(commit=False)

        p_transforms = "_".join([
            t.split("_")[1]
            for t in sorted(self.cleaned_data['p_transforms'])
        ])

        instance.parameters = {
            'n_prototypes': self.cleaned_data['p_n_clusters'],
            'use_sprites': self.cleaned_data['p_use_background'],
            'transformation_sequence': p_transforms
        }

        if self.__dataset:
            instance.dataset = self.__dataset
        else:
            instance.dataset = ZippedDataset.objects.create(zip_file=self.cleaned_data['dataset_zip'])

        if commit:
            instance.save()

        return instance
    

class SavedClusteringForm(forms.ModelForm):
    class Meta:
        model = SavedClustering
        fields = ('name', 'clustering_data',)
        widgets = {
            'clustering_data': forms.HiddenInput()
        }
    
    def __init__(self, *args, **kwargs):
        self.__from_dti = kwargs.pop('from_dti', None)

        super().__init__(*args, **kwargs)

        if self.__from_dti:
            self.fields["name"].initial = self.__from_dti.name
    
    def save(self, commit=True):
        instance = super().save(commit=False)

        if self.__from_dti:
            instance.from_dti = self.__from_dti

        if commit:
            instance.save()

        return instance