# -*- coding: utf-8 -*-
"""
Generator PDF untuk "Riwayat Upload Excel — Olah Data" (data siswa hasil
olahan: No, Nama, Nilai Eksakta & Non-Eksakta, Izin, Sakit, Alpa). Memakai
kop surat resmi sekolah yang sama dengan Math Perbangku & Cluster K-Means
(lihat pdf_perbangku.py / pdf_cluster.py), supaya seluruh laporan yang
diunduh dari halaman Riwayat Laporan tampilannya konsisten.
"""
import io
import os

from django.conf import settings
from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
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
        name="Sel", parent=ss["Normal"], fontName="Helvetica", fontSize=9,
        textColor=GRAY_TEXT, leading=12,
    ))
    ss.add(ParagraphStyle(
        name="SelBold", parent=ss["Normal"], fontName="Helvetica-Bold", fontSize=9,
        textColor=BLACK, leading=12,
    ))
    ss.add(ParagraphStyle(
        name="SelHeader", parent=ss["Normal"], fontName="Helvetica-Bold",
        fontSize=8.7, textColor=colors.white, leading=11, alignment=TA_CENTER,
    ))
    ss.add(ParagraphStyle(
        name="TandaTanganKeterangan", parent=ss["Normal"], fontName="Helvetica",
        fontSize=9.5, textColor=GRAY_TEXT, alignment=TA_RIGHT, leading=13,
    ))
    ss.add(ParagraphStyle(
        name="TandaTanganNama", parent=ss["Normal"], fontName="Helvetica-Bold",
        fontSize=10, textColor=BLACK, alignment=TA_RIGHT, leading=13,
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


def _tabel_siswa(siswa_list, ss):
    header = ["No", "Nama", "Nilai Eksakta", "Nilai Non-Eksakta", "Izin", "Sakit", "Alpa"]
    col_widths = [1.2 * cm, 6.3 * cm, 2.9 * cm, 3 * cm, 2 * cm, 2 * cm, 2 * cm]

    data = [[Paragraph(h, ss["SelHeader"]) for h in header]]
    for i, s in enumerate(siswa_list, start=1):
        data.append([
            _p(i, ss["Sel"]),
            _p(s.get("nama"), ss["Sel"]),
            _p(_fmt_angka(s.get("eksakta")), ss["Sel"]),
            _p(_fmt_angka(s.get("nonekstakta")), ss["Sel"]),
            _p(_fmt_angka(s.get("izin"), 0), ss["Sel"]),
            _p(_fmt_angka(s.get("sakit"), 0), ss["Sel"]),
            _p(_fmt_angka(s.get("alpa"), 0), ss["Sel"]),
        ])

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
        ("ALIGN", (2, 1), (-1, -1), "CENTER"),
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
    canvas.drawString(2 * cm, 1.1 * cm, "GuruKelas \u00b7 Riwayat Upload Excel \u2014 Olah Data")
    canvas.drawRightString(lebar - 2 * cm, 1.1 * cm, f"Halaman {doc.page}")
    canvas.setStrokeColor(LINE)
    canvas.line(2 * cm, 1.5 * cm, lebar - 2 * cm, 1.5 * cm)
    canvas.restoreState()


def build_data_olahan_pdf(kelas_nama, siswa_list, generated_by, nama_file_asli=None,
                           tempat=TEMPAT_DEFAULT, nama_kepala_sekolah=NAMA_KEPALA_SEKOLAH,
                           tanggal=None):
    """
    kelas_nama: nama kelas, mis. "Kelas 1A"
    siswa_list: list of dict {nama, eksakta, nonekstakta, izin, sakit, alpa}
    generated_by: nama guru yang mengunduh laporan
    nama_file_asli: nama file Excel asli yang diupload (opsional, buat info)
    return: bytes isi file PDF
    """
    tanggal = tanggal or timezone.localtime(timezone.now())
    tanggal_teks = _tanggal_indonesia(tanggal)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=1.6 * cm, bottomMargin=2 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
        title=f"Riwayat Upload Excel - Olah Data - {kelas_nama or ''}",
    )
    ss = _styles()
    story = []

    story += _kop_surat(ss)

    info_rows = [
        [_p("Kelas", ss["SelBold"]), _p(kelas_nama or "\u2013", ss["Sel"])],
        [_p("File Excel Asli", ss["SelBold"]), _p(nama_file_asli or "\u2013", ss["Sel"])],
        [_p("Wali Kelas / Guru", ss["SelBold"]), _p(generated_by, ss["Sel"])],
        [_p("Jumlah Siswa", ss["SelBold"]), _p(len(siswa_list), ss["Sel"])],
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
    story.append(Spacer(1, 4))

    story.append(Paragraph("Data Siswa Hasil Olahan", ss["SeksiJudul"]))
    if siswa_list:
        story.append(_tabel_siswa(siswa_list, ss))
    else:
        story.append(Paragraph("Belum ada data siswa hasil olahan untuk kelas ini.", ss["Sel"]))

    story.append(Spacer(1, 34))
    story.append(_blok_tanda_tangan(tempat, tanggal_teks, nama_kepala_sekolah, ss))

    doc.build(
        story,
        onFirstPage=_header_footer,
        onLaterPages=_header_footer,
    )
    return buffer.getvalue()
