from django.db import models

# A simple model for a dataset made of a single .zip file
class ZippedDataset(models.Model):
    id = models.UUIDField(primary_key=True)
    
    zip_file = models.FileField(upload_to='datasets')
    created_on = models.DateTimeField(auto_now_add=True, editable=False)