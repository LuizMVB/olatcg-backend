# Generated by Django 3.2.25 on 2024-07-17 05:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='analysis',
            name='generated_from_analysis',
            field=models.OneToOneField(blank=True, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='generated_analysis', to='core.analysis'),
        ),
    ]
