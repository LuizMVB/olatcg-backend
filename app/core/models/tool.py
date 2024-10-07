from django.db import models

class Tool(models.Model):
    title = models.CharField(max_length=20, default='BioPython', unique=True)
    description = models.CharField(max_length=100, default=None)
