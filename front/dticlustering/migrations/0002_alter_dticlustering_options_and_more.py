# Generated by Django 4.2.6 on 2023-12-12 15:57

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dticlustering', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='dticlustering',
            options={'ordering': ['-requested_on'], 'permissions': [('monitor_dticlustering', 'Can monitor DTI Clustering')]},
        ),
        migrations.AddField(
            model_name='dticlustering',
            name='requested_by',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.RemoveField(
            model_name="dticlustering",
            name="notify_email",
        ),
        migrations.AddField(
            model_name='dticlustering',
            name='notify_email',
            field=models.BooleanField(blank=True, default=False, help_text='Send an email when the clustering is finished', verbose_name='Notify by email'),
        ),
    ]