from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0002_siswa_alpa_siswa_eksakta_siswa_izin_siswa_nis_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="siswa",
            name="cluster_raw",
            field=models.IntegerField(
                blank=True,
                null=True,
                help_text="ID cluster mentah dari KMeans (0/1/2) sebelum dilabeli",
            ),
        ),
    ]
