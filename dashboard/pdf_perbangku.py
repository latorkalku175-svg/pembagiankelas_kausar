# -*- coding: utf-8 -*-
"""
Generator PDF untuk laporan "Math Perbangku" (hasil pengaturan tempat duduk
per meja). Memakai kop surat resmi sekolah (sama seperti Format_F4 - KOP
Master.docx) di bagian atas, tabel hasil pemasangan per meja & nama siswa,
lalu blok tempat/tanggal + tanda tangan Kepala Sekolah di pojok kanan bawah.
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
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, KeepTogether,
)

BRAND = colors.HexColor("#111827")       # jadi hitam gelap
BRAND_DARK = colors.HexColor("#111827")  # jadi hitam gelap
GRAY_TEXT = colors.HexColor("#374151")
GRAY_MUTED = colors.HexColor("#6B7280")
ROW_ALT = colors.HexColor("#F3F4F6")
LINE = colors.HexColor("#9CA3AF")
BLACK = colors.HexColor("#111827")

LOGO_PATH = os.path.join(settings.BASE_DIR, "dashboard", "static", "dashboard", "img", "logo_sekolah.png")

# ---------------------------------------------------------------------------
# Identitas kop surat sekolah -- sesuaikan di sini kalau data sekolah berubah.
# ---------------------------------------------------------------------------
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
        name="JudulLaporan", parent=ss["Normal"], fontName="Helvetica-Bold",
        fontSize=13, textColor=BRAND_DARK, alignment=TA_CENTER, spaceBefore=4, spaceAfter=0,
    ))
    ss.add(ParagraphStyle(
        name="SubJudulLaporan", parent=ss["Normal"], fontName="Helvetica",
        fontSize=9.5, textColor=GRAY_MUTED, alignment=TA_CENTER, spaceAfter=0,
    ))
    ss.add(ParagraphStyle(
        name="Meta", parent=ss["Normal"], fontName="Helvetica", fontSize=9,
        textColor=GRAY_TEXT, alignment=TA_LEFT,
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


def _kop_surat(ss):
    """Kop surat resmi sekolah -- logo di kiri, identitas sekolah di tengah,
    lalu garis ganda pemisah, meniru Format_F4 - KOP Master.docx."""
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


def _status_label(status):
    return {"paham": "Paham", "cukup": "Cukup", "kurang": "Kurang"}.get(status, status or "\u2013")


def _cluster_label(siswa):
    mapping = {"cerdas": "Cerdas", "pintar": "Pintar", "malas": "Malas"}
    return mapping.get(getattr(siswa, "cluster_label", None), "Belum di-cluster")


def _tabel_meja(meja_list, ss):
    header = ["Meja", "Nama Siswa", "Kategori Cluster", "Nilai Eksakta", "Nilai Non Eksakta", "Kelas"]
    data = [[Paragraph(h, ss["SelHeader"]) for h in header]]

    baris_span = []  # (start_row, end_row) untuk kolom yang perlu di-span (meja)
    row_idx = 1
    for meja in meja_list:
        siswa_di_meja = meja["siswa"]
        jumlah = len(siswa_di_meja) or 1
        start_row = row_idx
        for s in siswa_di_meja:
            nilai_eksakta = s.eksakta if s.eksakta is not None else s.nilai_matematika
            nilai_noneksakta = s.nonekstakta if s.nonekstakta is not None else s.nilai_bahasa
            data.append([
                _p(meja["nomor"], ss["SelBold"]) if s is siswa_di_meja[0] else "",
                _p(s.nama, ss["Sel"]),
                _p(_cluster_label(s), ss["Sel"]),
                _p(f"{nilai_eksakta:g}", ss["Sel"]),
                _p(f"{nilai_noneksakta:g}", ss["Sel"]),
                _p(s.kelas.nama if s.kelas else "\u2013", ss["Sel"]),
            ])
            row_idx += 1
        end_row = row_idx - 1
        if end_row > start_row:
            baris_span.append((start_row, end_row))

    col_widths = [1.6 * cm, 5.4 * cm, 3.4 * cm, 2.8 * cm, 2.4 * cm, 3.1 * cm]
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
        ("ALIGN", (3, 1), (3, -1), "CENTER"),
        ("ALIGN", (4, 1), (4, -1), "CENTER"),
        ("ALIGN", (5, 1), (5, -1), "CENTER"),
    ]
    for start, end in baris_span:
        style.append(("SPAN", (0, start), (0, end)))
    for i in range(1, len(data), 2):
        style.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))
    table.setStyle(TableStyle(style))
    return table


def _blok_tanda_tangan(tempat, tanggal_teks, nama_kepsek, ss):
    """Tempat/tanggal + tanda tangan Kepala Sekolah, rata kanan di pojok kanan bawah."""
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
    canvas.drawString(2 * cm, 1.1 * cm, "GuruKelas \u00b7 Laporan Math Perbangku")
    canvas.drawRightString(lebar - 2 * cm, 1.1 * cm, f"Halaman {doc.page}")
    canvas.setStrokeColor(LINE)
    canvas.line(2 * cm, 1.5 * cm, lebar - 2 * cm, 1.5 * cm)
    canvas.restoreState()


def build_perbangku_pdf(kelas, meja_list, rata_rata_kelas, generated_by,
                         tempat=TEMPAT_DEFAULT, nama_kepala_sekolah=NAMA_KEPALA_SEKOLAH,
                         tanggal=None):
    """
    kelas: objek Kelas
    meja_list: list of {"nomor", "siswa": [Siswa, ...], "rata_rata", "status"}
    rata_rata_kelas: float rata-rata nilai matematika seluruh kelas
    generated_by: nama guru yang mengunduh laporan
    return: bytes isi file PDF
    """
    tanggal = tanggal or timezone.localtime(timezone.now())
    tanggal_teks = _tanggal_indonesia(tanggal)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=1.6 * cm, bottomMargin=2 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
        title=f"Laporan Math Perbangku - {kelas.nama if kelas else ''}",
    )
    ss = _styles()
    story = []

    story += _kop_surat(ss)

    story.append(Paragraph("DATA HASIL PEMBAGIAN KELAS", ss["JudulLaporan"]))
    story.append(Paragraph("", ss["SubJudulLaporan"]))
    story.append(Spacer(1, 12))

    total_siswa = sum(len(m["siswa"]) for m in meja_list)
    total_meja = len(meja_list)
    info_rows = [
        [_p("Kelas", ss["SelBold"]), _p(kelas.nama if kelas else "\u2013", ss["Sel"])],
        [_p("Wali Kelas / Guru", ss["SelBold"]), _p(generated_by, ss["Sel"])],
        [_p("Jumlah Siswa", ss["SelBold"]), _p(total_siswa, ss["Sel"])],
        [_p("Jumlah Meja", ss["SelBold"]), _p(total_meja, ss["Sel"])],
        [_p("Rata-rata Nilai Matematika Kelas", ss["SelBold"]),
         _p(rata_rata_kelas if rata_rata_kelas is not None else "\u2013", ss["Sel"])],
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

    story.append(Paragraph("", ss["SeksiJudul"]))
    if meja_list:
        story.append(_tabel_meja(meja_list, ss))
    else:
        story.append(Paragraph("Belum ada data siswa/pengaturan meja di kelas ini.", ss["Sel"]))

    story.append(Spacer(1, 34))
    story.append(KeepTogether(_blok_tanda_tangan(tempat, tanggal_teks, nama_kepala_sekolah, ss)))

    doc.build(
        story,
        onFirstPage=_header_footer,
        onLaterPages=_header_footer,
    )
    return buffer.getvalue()
