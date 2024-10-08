# Generated by Django 3.2.25 on 2024-10-10 07:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_auto_20241008_1657'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blastninput',
            name='input_file',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='blastnoutput',
            name='output_file',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='fasttreeinput',
            name='input_file',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='fasttreeoutput',
            name='output_file',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='muscleinput',
            name='input_file',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='muscleoutput',
            name='output_file',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
