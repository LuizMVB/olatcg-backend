# Generated by Django 3.2.25 on 2024-07-17 19:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20240717_0519'),
    ]

    operations = [
        migrations.AlterField(
            model_name='analysis',
            name='experiment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='analyses', to='core.experiment'),
        ),
        migrations.AlterField(
            model_name='analysis',
            name='status',
            field=models.CharField(blank=True, choices=[('STARTED', 'Started'), ('FAILED', 'Failed'), ('FINISHED', 'Finished')], default='STARTED', max_length=14),
        ),
    ]
