from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0004_profilguru_foto'),
    ]

    operations = [
        migrations.AddField(
            model_name='profilguru',
            name='gelar',
            field=models.CharField(blank=True, default='', help_text='Contoh: S.Pd., M.Pd.', max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='profilguru',
            name='wali_kelas',
            field=models.CharField(blank=True, default='', help_text='Contoh: 1B, 2A', max_length=50),
            preserve_default=False,
        ),
    ]
