from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from .models import Kelas, Siswa, MateriUpload, ProfilGuru


INPUT_CLASS = (
    "w-full rounded-xl border border-gray-200 px-4 py-2.5 text-sm text-gray-700 "
    "focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 "
    "placeholder:text-gray-400"
)


class LoginForm(forms.Form):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "Masukkan username"}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"class": INPUT_CLASS, "placeholder": "Masukkan password"}),
    )


class GuruPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": INPUT_CLASS, "placeholder": "Masukkan email akun Anda"}),
    )


class GuruSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="Password Baru",
        widget=forms.PasswordInput(attrs={"class": INPUT_CLASS, "placeholder": "Masukkan password baru"}),
    )
    new_password2 = forms.CharField(
        label="Konfirmasi Password Baru",
        widget=forms.PasswordInput(attrs={"class": INPUT_CLASS, "placeholder": "Ulangi password baru"}),
    )


class KelasForm(forms.ModelForm):
    class Meta:
        model = Kelas
        fields = ["nama"]
        widgets = {
            "nama": forms.TextInput(attrs={
                "class": INPUT_CLASS, "placeholder": "Contoh: Kelas 1A"
            }),
        }
        labels = {"nama": "Nama Kelas"}


class SiswaForm(forms.ModelForm):
    class Meta:
        model = Siswa
        fields = [
            "nama", "nomor_meja", "nilai_matematika",
            "nilai_bahasa", "kehadiran_persen", "keaktifan",
        ]
        labels = {
            "nama": "Nama Siswa",
            "nomor_meja": "Nomor Meja",
            "nilai_matematika": "Nilai Matematika",
            "nilai_bahasa": "Nilai Bahasa",
            "kehadiran_persen": "Kehadiran (%)",
            "keaktifan": "Keaktifan (0-100)",
        }
        widgets = {
            "nama": forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "Nama lengkap siswa"}),
            "nomor_meja": forms.NumberInput(attrs={"class": INPUT_CLASS, "min": 1}),
            "nilai_matematika": forms.NumberInput(attrs={"class": INPUT_CLASS, "min": 0, "max": 100}),
            "nilai_bahasa": forms.NumberInput(attrs={"class": INPUT_CLASS, "min": 0, "max": 100}),
            "kehadiran_persen": forms.NumberInput(attrs={"class": INPUT_CLASS, "min": 0, "max": 100}),
            "keaktifan": forms.NumberInput(attrs={"class": INPUT_CLASS, "min": 0, "max": 100}),
        }


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """FileField yang menerima banyak file sekaligus dari satu <input multiple>."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return [single_file_clean(data, initial)]


class UploadDataSiswaForm(forms.Form):
    """Upload banyak file Excel leger sekaligus -- 1 file = 1 kelas (1A, 1B, 2A, 2B, dst).
    Nama kelas dideteksi otomatis dari nama filenya."""

    files = MultipleFileField(
        label="File Excel Leger (boleh pilih banyak file sekaligus)",
        widget=MultipleFileInput(attrs={
            "class": "block w-full text-sm text-gray-600",
            "accept": ".xlsx,.xls",
            "multiple": True,
        }),
    )
    guru_tujuan = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        label="Upload untuk Guru",
        widget=forms.Select(attrs={"class": INPUT_CLASS}),
        help_text="Khusus superuser: pilih guru pemilik kelas tujuan upload ini.",
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None and user.is_superuser:
            self.fields["guru_tujuan"].queryset = User.objects.filter(is_active=True).order_by("username")
        else:
            del self.fields["guru_tujuan"]

    def clean_files(self):
        files = self.cleaned_data.get("files") or []
        for f in files:
            if not f.name.lower().endswith((".xlsx", ".xls")):
                raise forms.ValidationError(f"'{f.name}' bukan file Excel (.xlsx/.xls).")
        return files


class MateriUploadForm(forms.ModelForm):
    class Meta:
        model = MateriUpload
        fields = ["judul", "deskripsi", "file"]
        widgets = {
            "judul": forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "Judul materi"}),
            "deskripsi": forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "Deskripsi singkat (opsional)"}),
            "file": forms.ClearableFileInput(attrs={"class": "block w-full text-sm text-gray-600"}),
        }
        labels = {"judul": "Judul Materi", "deskripsi": "Deskripsi", "file": "Pilih File"}


class SiswaManualForm(forms.ModelForm):
    """Tambah 1 siswa secara manual, dipakai di halaman Upload sebagai jalan
    pintas kalau upload file Excel leger tidak berhasil/format filenya tidak
    sesuai. Fitur yang diminta sengaja sama persis dengan yang dipakai
    K-Means (lihat dashboard/clustering.py): Eksakta, Non-Eksakta, Izin,
    Sakit, Alpa -- supaya siswa yang ditambah manual tetap ikut clustering
    dengan cara yang sama seperti hasil import Excel."""

    class Meta:
        model = Siswa
        fields = ["nama", "nomor_meja", "eksakta", "nonekstakta", "izin", "sakit", "alpa"]
        labels = {
            "nama": "Nama Siswa",
            "nomor_meja": "Nomor Meja (opsional)",
            "eksakta": "Nilai Eksakta (mis. Matematika)",
            "nonekstakta": "Nilai Non-Eksakta (rata-rata mapel lain)",
            "izin": "Jumlah Izin",
            "sakit": "Jumlah Sakit",
            "alpa": "Jumlah Alpa",
        }
        widgets = {
            "nama": forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "Nama lengkap siswa"}),
            "nomor_meja": forms.NumberInput(attrs={"class": INPUT_CLASS, "min": 1}),
            "eksakta": forms.NumberInput(attrs={"class": INPUT_CLASS, "min": 0, "max": 100, "step": "0.1"}),
            "nonekstakta": forms.NumberInput(attrs={"class": INPUT_CLASS, "min": 0, "max": 100, "step": "0.1"}),
            "izin": forms.NumberInput(attrs={"class": INPUT_CLASS, "min": 0}),
            "sakit": forms.NumberInput(attrs={"class": INPUT_CLASS, "min": 0}),
            "alpa": forms.NumberInput(attrs={"class": INPUT_CLASS, "min": 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nomor_meja"].required = False
        self.fields["eksakta"].required = True
        self.fields["nonekstakta"].required = True
        for nama_field in ("izin", "sakit", "alpa"):
            self.fields[nama_field].required = False


class ProfilGuruForm(forms.ModelForm):
    nama_lengkap = forms.CharField(
        label="Nama Lengkap", required=False,
        widget=forms.TextInput(attrs={"class": INPUT_CLASS}),
    )
    email = forms.EmailField(
        label="Email", required=False,
        widget=forms.EmailInput(attrs={"class": INPUT_CLASS}),
    )

    class Meta:
        model = ProfilGuru
        fields = ["sapaan", "gelar", "sekolah", "wali_kelas", "notifikasi_email", "foto"]
        labels = {"sapaan": "Sapaan", "gelar": "Gelar", "sekolah": "Nama Sekolah", "wali_kelas": "Wali Kelas", "notifikasi_email": "Terima notifikasi via email"}
        widgets = {
            "sapaan": forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "Contoh: Bu, Pak"}),
            "gelar": forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "Contoh: S.Pd., M.Pd."}),
            "sekolah": forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "Nama sekolah"}),
            "wali_kelas": forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "Contoh: 1B, 2A"}),
            "notifikasi_email": forms.CheckboxInput(attrs={
                "class": "h-4 w-4 rounded border-gray-300 text-indigo-500 focus:ring-indigo-400"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["nama_lengkap"].initial = self.instance.user.get_full_name()
            self.fields["email"].initial = self.instance.user.email

    def save(self, commit=True):
        profil = super().save(commit=commit)
        if commit:
            user = profil.user
            full_name = self.cleaned_data.get("nama_lengkap", "")
            if full_name:
                parts = full_name.split(" ", 1)
                user.first_name = parts[0]
                user.last_name = parts[1] if len(parts) > 1 else ""
            user.email = self.cleaned_data.get("email", "")
            user.save()
        return profil
