from django.contrib import admin
from .models import (
    Kelas, Siswa, RiwayatUploadXlsx, RiwayatPerbangku, RiwayatClusterKmeans, ProfilGuru,
)


@admin.register(Kelas)
class KelasAdmin(admin.ModelAdmin):
    list_display = ("nama", "guru", "jumlah_siswa", "dibuat_pada")
    search_fields = ("nama",)


@admin.register(Siswa)
class SiswaAdmin(admin.ModelAdmin):
    list_display = (
        "nama", "kelas", "nomor_meja", "nilai_matematika",
        "nilai_bahasa", "kehadiran_persen", "keaktifan", "cluster_label",
    )
    list_filter = ("kelas", "cluster_label")
    search_fields = ("nama",)


@admin.register(RiwayatUploadXlsx)
class RiwayatUploadXlsxAdmin(admin.ModelAdmin):
    list_display = ("nama_file", "kelas", "diupload_oleh", "jumlah_siswa", "diupload_pada")
    list_filter = ("kelas", "diupload_oleh")
    search_fields = ("nama_file", "kelas__nama")
    ordering = ("-diupload_pada",)


@admin.register(RiwayatPerbangku)
class RiwayatPerbangkuAdmin(admin.ModelAdmin):
    list_display = ("kelas", "diatur_oleh", "jumlah_meja", "jumlah_siswa", "diatur_pada")
    list_filter = ("kelas", "diatur_oleh")
    search_fields = ("kelas__nama",)
    ordering = ("-diatur_pada",)


@admin.register(RiwayatClusterKmeans)
class RiwayatClusterKmeansAdmin(admin.ModelAdmin):
    list_display = (
        "judul_kelas", "kelas", "dijalankan_oleh", "jumlah_siswa",
        "jumlah_cerdas", "jumlah_pintar", "jumlah_malas", "sumber", "dijalankan_pada",
    )
    list_filter = ("kelas", "sumber", "dijalankan_oleh")
    search_fields = ("kelas__nama", "judul_kelas")
    ordering = ("-dijalankan_pada",)


@admin.register(ProfilGuru)
class ProfilGuruAdmin(admin.ModelAdmin):
    list_display = ("user", "sapaan", "sekolah")
