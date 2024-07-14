# Generated by Django 3.2.25 on 2024-07-12 15:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Alignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Analysis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=20)),
                ('description', models.CharField(max_length=100)),
                ('type', models.CharField(choices=[('ALIGNMENT', 'Alignment'), ('HOMOLOGY', 'Homology')], default='ALIGNMENT', max_length=14)),
                ('status', models.CharField(choices=[('STARTED', 'Started'), ('FAILED', 'Failed'), ('FINISHED', 'Finished')], default='STARTED', max_length=14)),
            ],
        ),
        migrations.CreateModel(
            name='BiologicalSequence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Taxonomy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='HomologyAnalysis',
            fields=[
                ('analysis', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='core.analysis')),
                ('newick', models.CharField(max_length=700)),
            ],
        ),
    ]
