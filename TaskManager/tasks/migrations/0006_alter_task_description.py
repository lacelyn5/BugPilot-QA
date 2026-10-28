from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tasks", "0005_task_due_date_task_priority"),
    ]

    operations = [
        migrations.AlterField(
            model_name="task",
            name="description",
            field=models.TextField(blank=True),
        ),
    ]
