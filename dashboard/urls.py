from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views
from .forms import GuruPasswordResetForm, GuruSetPasswordForm

app_name = "dashboard"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # ----- Lupa Password (kirim link reset via email Gmail) -----
    path(
        "lupa-password/",
        auth_views.PasswordResetView.as_view(
            template_name="dashboard/auth/password_reset_form.html",
            email_template_name="dashboard/auth/password_reset_email.html",
            subject_template_name="dashboard/auth/password_reset_subject.txt",
            form_class=GuruPasswordResetForm,
            success_url=reverse_lazy("dashboard:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "lupa-password/terkirim/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="dashboard/auth/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset-password/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="dashboard/auth/password_reset_confirm.html",
            form_class=GuruSetPasswordForm,
            success_url=reverse_lazy("dashboard:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset-password/selesai/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="dashboard/auth/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),

    path("", views.beranda, name="beranda"),
    path("kelas/pilih/<int:kelas_id>/", views.pilih_kelas, name="pilih_kelas"),

    path("kelas/", views.kelas_list_view, name="kelas_list"),
    path("kelas/<int:kelas_id>/", views.kelas_detail_view, name="kelas_detail"),
    path("kelas/<int:kelas_id>/hapus/", views.kelas_hapus_view, name="kelas_hapus"),
    path("kelas/<int:kelas_id>/siswa/<int:siswa_id>/edit/", views.siswa_edit_view, name="siswa_edit"),
    path("kelas/<int:kelas_id>/siswa/<int:siswa_id>/hapus/", views.siswa_hapus_view, name="siswa_hapus"),

    path("cluster/", views.cluster_overview, name="cluster_overview"),
    path("cluster/jalankan/", views.cluster_jalankan, name="cluster_jalankan"),
    path("cluster/unduh-pdf/", views.cluster_pdf_view, name="cluster_pdf"),
    path("cluster/preview-pdf/", views.cluster_pdf_preview_view, name="cluster_pdf_preview"),
    path("cluster/naik-kelas/", views.naik_kelas_view, name="naik_kelas"),
    path("cluster/naik-kelas/proses/", views.naik_kelas_proses_view, name="naik_kelas_proses"),
    path("cluster/<str:label>/", views.cluster_detail, name="cluster_detail"),

    path("math-perbangku/", views.math_perbangku, name="math_perbangku"),
    path("math-perbangku/atur/", views.math_perbangku_atur, name="math_perbangku_atur"),
    path("math-perbangku/unduh-pdf/", views.math_perbangku_pdf_view, name="math_perbangku_pdf"),
    path("math-perbangku/preview-pdf/", views.math_perbangku_pdf_preview_view, name="math_perbangku_pdf_preview"),

    path("upload-file/", views.upload_file_view, name="upload_file"),
    path("upload-file/latih-kmeans/", views.upload_data_siswa_view, name="upload_data_siswa"),
    path("upload-file/tambah-siswa/", views.tambah_siswa_manual_view, name="tambah_siswa_manual"),
    path("upload-file/<int:materi_id>/hapus/", views.materi_hapus_view, name="materi_hapus"),

    path("laporan/", views.laporan_view, name="laporan"),
    path("laporan/riwayat/<int:riwayat_id>/unduh-asli/", views.riwayat_unduh_asli_view, name="riwayat_unduh_asli"),
    path("laporan/riwayat/<int:riwayat_id>/unduh-olahan/", views.riwayat_unduh_olahan_view, name="riwayat_unduh_olahan"),
    path("laporan/riwayat/<int:riwayat_id>/preview-asli/", views.riwayat_preview_asli_view, name="riwayat_preview_asli"),
    path("laporan/riwayat/<int:riwayat_id>/preview-olahan/", views.riwayat_preview_olahan_view, name="riwayat_preview_olahan"),
    path("laporan/riwayat-perbangku/<int:riwayat_id>/unduh/", views.riwayat_unduh_perbangku_view, name="riwayat_unduh_perbangku"),
    path("laporan/riwayat-perbangku/<int:riwayat_id>/preview/", views.riwayat_preview_perbangku_view, name="riwayat_preview_perbangku"),
    path("laporan/riwayat-cluster/<int:riwayat_id>/unduh/", views.riwayat_unduh_cluster_view, name="riwayat_unduh_cluster"),
    path("laporan/riwayat-cluster/<int:riwayat_id>/preview/", views.riwayat_preview_cluster_view, name="riwayat_preview_cluster"),
    path("pengaturan/", views.pengaturan_view, name="pengaturan"),
    path("pengaturan/upload-foto/", views.upload_foto_guru, name="upload_foto_guru"),
    path("pengaturan/hapus-akun/", views.hapus_akun_view, name="hapus_akun"),

    # PWA
    path("sw.js", views.service_worker, name="service_worker"),
]
