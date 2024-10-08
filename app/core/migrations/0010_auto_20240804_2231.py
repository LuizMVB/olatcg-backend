# Generated by Django 3.2.25 on 2024-08-04 22:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_auto_20240731_2150'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxonomy',
            name='class_name',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='taxonomy',
            name='family',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='taxonomy',
            name='genus',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='taxonomy',
            name='kingdom',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='taxonomy',
            name='order',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='taxonomy',
            name='phylum',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='taxonomy',
            name='species',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='taxonomy',
            name='tax_external_id',
            field=models.IntegerField(null=True),
        ),
    ]
