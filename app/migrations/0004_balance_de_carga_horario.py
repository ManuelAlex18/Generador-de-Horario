# Generated by Django 5.1 on 2024-09-20 20:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_balance_de_carga_alter_asignatura_nombre'),
    ]

    operations = [
        migrations.AddField(
            model_name='balance_de_carga',
            name='Horario',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='app.horario'),
            preserve_default=False,
        ),
    ]
