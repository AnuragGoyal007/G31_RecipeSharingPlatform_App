# Generated by Django 5.2 on 2025-04-16 18:42

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipe_app', '0004_remove_recipe_liked_by_like'),
    ]

    operations = [
        migrations.AlterField(
            model_name='like',
            name='recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes_set', to='recipe_app.recipe'),
        ),
    ]
