# Generated by Django 3.2.25 on 2024-07-12 16:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_auto_20240712_1604'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tool',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(default='ALIGNMENT', max_length=20, unique=True)),
                ('description', models.CharField(default=None, max_length=100)),
            ],
        ),
        migrations.RemoveField(
            model_name='analysis',
            name='type',
        ),
        migrations.AddField(
            model_name='analysis',
            name='tools',
            field=models.ManyToManyField(related_name='analyses', to='core.Tool'),
        ),
    ]
