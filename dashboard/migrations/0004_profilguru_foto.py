from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0003_siswa_cluster_raw'),
    ]

    operations = [
        migrations.AddField(
            model_name='profilguru',
            name='foto',
            field=models.ImageField(blank=True, null=True, upload_to='foto_guru/'),
        ),
    ]
