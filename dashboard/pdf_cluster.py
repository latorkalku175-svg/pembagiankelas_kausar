# -*- coding: utf-8 -*-
"""
Generator PDF untuk laporan "Cluster K-Means" (hasil pengelompokan siswa
menjadi Cerdas/Pintar/Malas). Memakai kop surat resmi sekolah yang sama
dengan Math Perbangku (lihat pdf_perbangku.py), lalu ringkasan jumlah per
kategori dan tabel hasil per siswa.
"""
import io
import os

from django.conf import settings
from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image,
)

BRAND = colors.HexColor("#111827")
BRAND_DARK = colors.HexColor("#111827")
GRAY_TEXT = colors.HexColor("#374151")
GRAY_MUTED = colors.HexColor("#6B7280")
ROW_ALT = colors.HexColor("#F3F4F6")
LINE = colors.HexColor("#9CA3AF")
BLACK = colors.HexColor("#111827")

WARNA_CERDAS = colors.HexColor("#15803D")
WARNA_PINTAR = colors.HexColor("#4338CA")
WARNA_MALAS = colors.HexColor("#C2410C")

LOGO_PATH = os.path.join(settings.BASE_DIR, "dashboard", "static", "dashboard", "img", "logo_sekolah.png")

KOP_BARIS = [
    "PEMERINTAH PROVINSI DAERAH KHUSUS IBUKOTA JAKARTA",
    "DINAS PENDIDIKAN",
    "SEKOLAH DASAR NEGERI KEBAYORAN LAMA UTARA 09 PAGI",
]
KOP_ALAMAT = (
    "Jl. Delman Asri IX No.15 Kecamatan Kebayoran Lama Jakarta Selatan &nbsp;&nbsp;"
    "Telp. 021-7239610 &nbsp;&nbsp; Email: sdnklu09@gmail.com &nbsp;&nbsp; Kode Pos: 12240"
)

NAMA_KEPALA_SEKOLAH = "Nurmiyati, S.Pd."
TEMPAT_DEFAULT = "Jakarta"

BULAN_ID = [
    "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]

LABEL_KATEGORI = {"cerdas": "Cerdas", "pintar": "Pintar", "malas": "Malas"}


def _tanggal_indonesia(dt):
    return f"{dt.day} {BULAN_ID[dt.month]} {dt.year}"


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle(
        name="KopUtama", parent=ss["Normal"], fontName="Helvetica-Bold",
        fontSize=13.5, textColor=BLACK, alignment=TA_CENTER, leading=16,
    ))
    ss.add(ParagraphStyle(
        name="KopSub", parent=ss["Normal"], fontName="Helvetica-Bold",
        fontSize=11.5, textColor=BLACK, alignment=TA_CENTER, leading=14,
    ))
    ss.add(ParagraphStyle(
        name="KopAlamat", parent=ss["Normal"], fontName="Helvetica",
        fontSize=8, textColor=BLACK, alignment=TA_CENTER, leading=10,
    ))
    ss.add(ParagraphStyle(
        name="SeksiJudul", parent=ss["Heading2"], fontName="Helvetica-Bold",
        fontSize=12, textColor=BLACK, spaceBefore=12, spaceAfter=4,
    ))
    ss.add(ParagraphStyle(
        name="Sel", parent=ss["Normal"], fontName="Helvetica", fontSize=8.7,
        textColor=GRAY_TEXT, leading=11,
    ))
    ss.add(ParagraphStyle(
        name="SelBold", parent=ss["Normal"], fontName="Helvetica-Bold", fontSize=8.7,
        textColor=BLACK, leading=11,
    ))
    ss.add(ParagraphStyle(
        name="SelHeader", parent=ss["Normal"], fontName="Helvetica-Bold",
        fontSize=8.3, textColor=colors.white, leading=11, alignment=TA_CENTER,
    ))
    ss.add(ParagraphStyle(
        name="TandaTanganKeterangan", parent=ss["Normal"], fontName="Helvetica",
        fontSize=9.5, textColor=GRAY_TEXT, alignment=TA_RIGHT, leading=13,
    ))
    ss.add(ParagraphStyle(
        name="TandaTanganNama", parent=ss["Normal"], fontName="Helvetica-Bold",
        fontSize=10, textColor=BLACK, alignment=TA_RIGHT, leading=13,
    ))
    ss.add(ParagraphStyle(
        name="LabelKecil", parent=ss["Normal"], fontName="Helvetica",
        fontSize=7.7, textColor=GRAY_MUTED,
    ))
    ss.add(ParagraphStyle(
        name="NilaiBesar", parent=ss["Normal"], fontName="Helvetica-Bold",
        fontSize=17, textColor=colors.HexColor("#111827"),
    ))
    return ss


def _p(text, style):
    if text is None or text == "":
        text = "\u2013"
    return Paragraph(str(text), style)


def _fmt_angka(v, digit=1):
    if v is None:
        return "\u2013"
    try:
        return f"{float(v):.{digit}f}"
    except (TypeError, ValueError):
        return str(v)


def _kop_surat(ss):
    teks_cells = [
        Paragraph(KOP_BARIS[0], ss["KopUtama"]),
        Paragraph(KOP_BARIS[1], ss["KopSub"]),
        Paragraph(KOP_BARIS[2], ss["KopSub"]),
        Spacer(1, 2),
        Paragraph(KOP_ALAMAT, ss["KopAlamat"]),
    ]

    if os.path.exists(LOGO_PATH):
        logo = Image(LOGO_PATH, width=2.1 * cm, height=2.55 * cm)
    else:
        logo = Spacer(2.1 * cm, 2.55 * cm)

    tabel = Table(
        [[logo, teks_cells]],
        colWidths=[2.6 * cm, 14.4 * cm],
    )
    tabel.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    garis_tebal = Table([[""]], colWidths=[17 * cm], rowHeights=[2.5])
    garis_tebal.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 2.2, BLACK)]))
    garis_tipis = Table([[""]], colWidths=[17 * cm], rowHeights=[2])
    garis_tipis.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 0.6, BLACK)]))

    return [tabel, Spacer(1, 6), garis_tebal, Spacer(1, 1.5), garis_tipis, Spacer(1, 14)]


def _kartu_ringkasan(ringkasan, ss):
    """Kartu jumlah Cerdas / Pintar / Malas, berwarna sesuai kategori."""
    def _sel(label, warna, jumlah):
        return [
            Paragraph(label.upper(), ParagraphStyle(
                name=f"Label_{label}", parent=ss["LabelKecil"], textColor=warna,
                fontName="Helvetica-Bold",
            )),
            Spacer(1, 3),
            Paragraph(str(jumlah), ss["NilaiBesar"]),
            Paragraph("siswa", ss["LabelKecil"]),
        ]

    cells = [
        _sel("Cerdas", WARNA_CERDAS, ringkasan.get("cerdas", 0)),
        _sel("Pintar", WARNA_PINTAR, ringkasan.get("pintar", 0)),
        _sel("Malas", WARNA_MALAS, ringkasan.get("malas", 0)),
    ]
    lebar_kolom = (17 * cm) / 3
    table = Table([cells], colWidths=[lebar_kolom] * 3)
    table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.75, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.75, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table


def _tabel_siswa(siswa_snapshot, ss, tampilkan_kolom_kelas):
    if tampilkan_kolom_kelas:
        header = ["No", "Kelas", "Nama", "Kategori", "Eksakta", "Non-Eksakta", "Rangking", "Skor Akademik", "Skor Disiplin"]
        col_widths = [1 * cm, 2.1 * cm, 4 * cm, 2.1 * cm, 1.9 * cm, 2.1 * cm, 1.7 * cm, 2.05 * cm, 2.05 * cm]
    else:
        header = ["No", "Nama", "Kategori", "Eksakta", "Non-Eksakta", "Rangking", "Skor Akademik", "Skor Disiplin"]
        col_widths = [1 * cm, 5 * cm, 2.3 * cm, 2.1 * cm, 2.3 * cm, 1.9 * cm, 2.2 * cm, 2.2 * cm]

    data = [[Paragraph(h, ss["SelHeader"]) for h in header]]
    for i, s in enumerate(siswa_snapshot, start=1):
        baris = [_p(i, ss["Sel"])]
        if tampilkan_kolom_kelas:
            baris.append(_p(s.get("kelas_nama"), ss["Sel"]))
        baris += [
            _p(s.get("nama"), ss["Sel"]),
            _p(LABEL_KATEGORI.get(s.get("cluster_label"), "Belum di-cluster"), ss["Sel"]),
            _p(_fmt_angka(s.get("eksakta")), ss["Sel"]),
            _p(_fmt_angka(s.get("nonekstakta")), ss["Sel"]),
            _p(_fmt_angka(s.get("rangking"), 0), ss["Sel"]),
            _p(_fmt_angka(s.get("skor_akademik"), 3), ss["Sel"]),
            _p(_fmt_angka(s.get("skor_disiplin"), 3), ss["Sel"]),
        ]
        data.append(baris)

    table = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), BRAND),
        ("TOPPADDING", (0, 0), (-1, 0), 7),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
        ("TOPPADDING", (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, 0), 0.75, BRAND_DARK),
        ("GRID", (0, 1), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 1), (0, -1), "CENTER"),
    ]
    for i in range(1, len(data), 2):
        style.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))
    table.setStyle(TableStyle(style))
    return table


def _blok_tanda_tangan(tempat, tanggal_teks, nama_kepsek, ss):
    kiri = Spacer(1, 1)
    kanan = [
        Paragraph(f"{tempat}, {tanggal_teks}", ss["TandaTanganKeterangan"]),
        Paragraph("Mengetahui,", ss["TandaTanganKeterangan"]),
        Paragraph("Kepala Sekolah", ss["TandaTanganKeterangan"]),
        Spacer(1, 60),
        Paragraph(f"<u>{nama_kepsek}</u>", ss["TandaTanganNama"]),
    ]
    table = Table([[kiri, kanan]], colWidths=[9.5 * cm, 7.5 * cm])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return table


def _header_footer(canvas, doc):
    canvas.saveState()
    lebar, tinggi = A4
    canvas.setFillColor(BRAND)
    canvas.rect(0, tinggi - 0.35 * cm, lebar, 0.35 * cm, stroke=0, fill=1)

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GRAY_MUTED)
    canvas.drawString(2 * cm, 1.1 * cm, "GuruKelas \u00b7 Laporan Cluster K-Means")
    canvas.drawRightString(lebar - 2 * cm, 1.1 * cm, f"Halaman {doc.page}")
    canvas.setStrokeColor(LINE)
    canvas.line(2 * cm, 1.5 * cm, lebar - 2 * cm, 1.5 * cm)
    canvas.restoreState()


def build_cluster_pdf(judul_kelas, siswa_snapshot, ringkasan, generated_by,
                       tempat=TEMPAT_DEFAULT, nama_kepala_sekolah=NAMA_KEPALA_SEKOLAH,
                       tanggal=None, tampilkan_kolom_kelas=None):
    """
    judul_kelas: judul kelas/tingkat, mis. "Kelas 1A dan 1B"
    siswa_snapshot: list of dict {nama, kelas_nama, cluster_label, eksakta,
        nonekstakta, rangking, skor_akademik, skor_disiplin}
    ringkasan: dict {"cerdas": n, "pintar": n, "malas": n}
    generated_by: nama guru yang mengunduh laporan
    tampilkan_kolom_kelas: True kalau siswa berasal dari >1 rombel (kolom
        "Kelas" ditampilkan); default: dideteksi otomatis dari data.
    return: bytes isi file PDF
    """
    tanggal = tanggal or timezone.localtime(timezone.now())
    tanggal_teks = _tanggal_indonesia(tanggal)

    if tampilkan_kolom_kelas is None:
        nama_kelas_unik = {s.get("kelas_nama") for s in siswa_snapshot if s.get("kelas_nama")}
        tampilkan_kolom_kelas = len(nama_kelas_unik) > 1

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=1.6 * cm, bottomMargin=2 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
        title=f"Laporan Cluster K-Means - {judul_kelas or ''}",
    )
    ss = _styles()
    story = []

    story += _kop_surat(ss)

    total_siswa = len(siswa_snapshot)
    info_rows = [
        [_p("Kelas / Tingkat", ss["SelBold"]), _p(judul_kelas or "\u2013", ss["Sel"])],
        [_p("Wali Kelas / Guru", ss["SelBold"]), _p(generated_by, ss["Sel"])],
        [_p("Jumlah Siswa", ss["SelBold"]), _p(total_siswa, ss["Sel"])],
        [_p("Tanggal Dicetak", ss["SelBold"]), _p(tanggal_teks, ss["Sel"])],
    ]
    info_table = Table(info_rows, colWidths=[5 * cm, 12 * cm])
    info_table.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 10))

    story.append(_kartu_ringkasan(ringkasan, ss))
    story.append(Spacer(1, 4))

    story.append(Paragraph("Hasil Pengelompokan K-Means per Siswa", ss["SeksiJudul"]))
    if siswa_snapshot:
        story.append(_tabel_siswa(siswa_snapshot, ss, tampilkan_kolom_kelas))
    else:
        story.append(Paragraph("Belum ada data hasil clustering untuk kelas ini.", ss["Sel"]))

    story.append(Spacer(1, 34))
    story.append(_blok_tanda_tangan(tempat, tanggal_teks, nama_kepala_sekolah, ss))

    doc.build(
        story,
        onFirstPage=_header_footer,
        onLaterPages=_header_footer,
    )
    return buffer.getvalue()
