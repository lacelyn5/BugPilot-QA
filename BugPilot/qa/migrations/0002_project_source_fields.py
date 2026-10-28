from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("qa", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="base_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="project",
            name="source_directory",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="project",
            name="source_archive",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
