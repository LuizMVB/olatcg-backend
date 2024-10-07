from django.db import models

class Experiment(models.Model):
    title = models.CharField(max_length=20, default=None)
    description = models.CharField(max_length=100, default=None)
