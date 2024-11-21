# Generated by Django 4.2.6 on 2024-11-19 12:54

from django.db import migrations, models
import django.db.models.deletion


def migrate_dataset(apps, schema_editor):
    Regions = apps.get_model("regions", "Regions")
    Dataset = apps.get_model("datasets", "Dataset")
    for region in Regions.objects.all():
        try:
            region.dataset = Dataset.objects.get(id=region.dataset_legacy_id)
            region.save()
        except Dataset.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ("datasets", "0005_better_dataset_model"),
        ("regions", "0003_regions_regions"),
    ]

    operations = [
        migrations.RenameField(
            model_name="regions",
            old_name="dataset",
            new_name="dataset_legacy",
        ),
        migrations.AddField(
            model_name="regions",
            name="dataset",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="datasets.dataset",
            ),
        ),
        migrations.RunPython(migrate_dataset, reverse_code=migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="regions",
            name="dataset_legacy",
        ),
    ]