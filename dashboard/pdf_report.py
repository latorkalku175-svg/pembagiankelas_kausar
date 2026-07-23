# -*- coding: utf-8 -*-
"""
Generator PDF untuk halaman "Riwayat Laporan".

Dibuat terpisah dari views.py supaya urusan tata-letak/gaya PDF tidak
bercampur dengan logic Django view. Memakai reportlab langsung (bukan
render-HTML-ke-PDF) supaya:
  - Tidak perlu library sistem tambahan (aman untuk deploy di Render/Heroku).
  - Struktur tabel & halaman lebih presisi dan konsisten rapinya.
"""
import io

from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
)

# Warna brand GuruKelas (samakan dengan tailwind.config di base.html)
BRAND = colors.HexColor("#6C5CE7")
BRAND_DARK = colors.HexColor("#4A3CB8")
BRAND_SOFT = colors.HexColor("#F1F0FE")
GRAY_TEXT = colors.HexColor("#374151")
GRAY_MUTED = colors.HexColor("#9CA3AF")
ROW_ALT = colors.HexColor("#FAFAFB")
LINE = colors.HexColor("#E5E7EB")


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle(
        name="JudulUtama", parent=ss["Title"], fontName="Helvetica-Bold",
        fontSize=20, textColor=BRAND_DARK, spaceAfter=2,
    ))
    ss.add(ParagraphStyle(
        name="SubJudul", parent=ss["Normal"], fontName="Helvetica",
        fontSize=10, textColor=GRAY_MUTED, spaceAfter=0,
    ))
    ss.add(ParagraphStyle(
        name="Meta", parent=ss["Normal"], fontName="Helvetica",
        fontSize=8.5, textColor=GRAY_MUTED, alignment=TA_RIGHT,
    ))
    ss.add(ParagraphStyle(
        name="SeksiJudul", parent=ss["Heading2"], fontName="Helvetica-Bold",
        fontSize=13, textColor=colors.HexColor("#111827"),
        spaceBefore=14, spaceAfter=2,
    ))
    ss.add(ParagraphStyle(
        name="SeksiKeterangan", parent=ss["Normal"], fontName="Helvetica",
        fontSize=9, textColor=GRAY_MUTED, spaceAfter=8,
    ))
    ss.add(ParagraphStyle(
        name="Sel", parent=ss["Normal"], fontName="Helvetica", fontSize=8.7,
        textColor=GRAY_TEXT, leading=11,
    ))
    ss.add(ParagraphStyle(
        name="SelHeader", parent=ss["Normal"], fontName="Helvetica-Bold",
        fontSize=8.3, textColor=colors.white, leading=11,
    ))
    ss.add(ParagraphStyle(
        name="KosongInfo", parent=ss["Normal"], fontName="Helvetica-Oblique",
        fontSize=9, textColor=GRAY_MUTED, alignment=1,
    ))
    return ss


def _p(text, style):
    """Bungkus teks jadi Paragraph supaya bisa wrap otomatis di dalam sel tabel."""
    if text is None or text == "":
        text = "–"
    return Paragraph(str(text), style)


def _fmt_dt(value, fmt="%d %b %Y, %H:%M"):
    if not value:
        return "–"
    try:
        return timezone.localtime(value).strftime(fmt)
    except Exception:
        return value.strftime(fmt)


def _fmt_d(value, fmt="%d %b %Y"):
    if not value:
        return "–"
    try:
        return timezone.localtime(value).strftime(fmt)
    except Exception:
        return value.strftime(fmt)


def _kartu_ringkasan(items, styles):
    """items: list of (label, value) -> render sebagai baris kartu ringkasan."""
    ss = styles
    cells = []
    for label, value in items:
        cell = [
            Paragraph(label, ParagraphStyle(
                name="LabelKecil", parent=ss["Normal"], fontName="Helvetica",
                fontSize=7.7, textColor=GRAY_MUTED,
            )),
            Spacer(1, 3),
            Paragraph(str(value), ParagraphStyle(
                name="NilaiBesar", parent=ss["Normal"], fontName="Helvetica-Bold",
                fontSize=15, textColor=colors.HexColor("#111827"),
            )),
        ]
        cells.append(cell)

    lebar_total = 17 * cm
    lebar_kolom = lebar_total / len(cells)
    table = Table([cells], colWidths=[lebar_kolom] * len(cells))
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (0, 0), 0.75, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.75, LINE),
        ("BOX", (0, 0), (-1, -1), 0.75, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table


def _tabel_data(header, rows, col_widths, styles, kosong_teks):
    ss = styles
    if not rows:
        data = [[Paragraph(h, ss["SelHeader"]) for h in header]]
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND),
            ("TOPPADDING", (0, 0), (-1, 0), 7),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("LINEBELOW", (0, 0), (-1, 0), 0.75, BRAND_DARK),
        ]))
        return [table, Spacer(1, 4), Paragraph(kosong_teks, ss["KosongInfo"])]

    data = [[Paragraph(h, ss["SelHeader"]) for h in header]]
    for row in rows:
        data.append([cell if isinstance(cell, Paragraph) else _p(cell, ss["Sel"]) for cell in row])

    table = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), BRAND),
        ("TOPPADDING", (0, 0), (-1, 0), 7),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, 0), 0.75, BRAND_DARK),
        ("LINEBELOW", (0, 1), (-1, -2), 0.5, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))
    table.setStyle(TableStyle(style))
    return [table]


def _header_footer(canvas, doc, judul_dokumen):
    canvas.saveState()
    lebar, tinggi = A4

    # Garis brand tipis di paling atas halaman
    canvas.setFillColor(BRAND)
    canvas.rect(0, tinggi - 0.35 * cm, lebar, 0.35 * cm, stroke=0, fill=1)

    # Footer: nama aplikasi (kiri) + nomor halaman (kanan)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GRAY_MUTED)
    canvas.drawString(2 * cm, 1.1 * cm, "GuruKelas · Riwayat Laporan")
    canvas.drawRightString(lebar - 2 * cm, 1.1 * cm, f"Halaman {doc.page}")
    canvas.setStrokeColor(LINE)
    canvas.line(2 * cm, 1.5 * cm, lebar - 2 * cm, 1.5 * cm)
    canvas.restoreState()


def build_laporan_pdf(data, generated_by, is_superuser):
    """
    data: dict hasil dari views._kumpulkan_data_laporan()
    return: bytes isi file PDF
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
        title="Riwayat Laporan - GuruKelas",
    )
    ss = _styles()
    story = []

    waktu_dibuat = _fmt_dt(timezone.now())

    story.append(Paragraph("Riwayat Laporan", ss["JudulUtama"]))
    story.append(Paragraph("GuruKelas · Riwayat aktivitas guru &amp; upload data", ss["SubJudul"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f"Dibuat pada {waktu_dibuat} oleh {generated_by}", ss["Meta"],
    ))
    story.append(Spacer(1, 14))

    if is_superuser:
        story.append(_kartu_ringkasan([
            ("TOTAL GURU", data.get("total_guru") or 0),
            ("TOTAL UPLOAD EXCEL", data.get("total_upload_excel") or 0),
            ("LOGIN TERAKHIR ANDA", _fmt_dt(data.get("terakhir_login_saya"))),
        ], ss))

        story.append(Paragraph("Riwayat Guru", ss["SeksiJudul"]))
        story.append(Paragraph(
            "Berapa kali tiap guru upload Excel, kapan terakhir login, dan sejak kapan bergabung.",
            ss["SeksiKeterangan"],
        ))
        rows = []
        for g in (data.get("guru_stats") or []):
            nama = g["user"].first_name or g["user"].username
            rows.append([
                _p(nama, ss["Sel"]),
                _p(g["jumlah_kelas"], ss["Sel"]),
                _p(g["jumlah_siswa"], ss["Sel"]),
                _p(g["jumlah_upload"], ss["Sel"]),
                _p(_fmt_dt(g["terakhir_login"]) if g["terakhir_login"] else "Belum pernah", ss["Sel"]),
                _p(_fmt_d(g["bergabung_sejak"]), ss["Sel"]),
            ])
        story += _tabel_data(
            header=["Guru", "Kelas", "Siswa", "Upload", "Terakhir Login", "Bergabung"],
            rows=rows,
            col_widths=[3.6 * cm, 1.8 * cm, 1.8 * cm, 1.8 * cm, 4 * cm, 3 * cm],
            styles=ss,
            kosong_teks="Belum ada guru terdaftar.",
        )
    else:
        story.append(_kartu_ringkasan([
            ("UPLOAD EXCEL ANDA", data.get("total_upload_excel") or 0),
            ("LOGIN TERAKHIR", _fmt_dt(data.get("terakhir_login_saya"))),
        ], ss))

    story.append(Paragraph("Riwayat Upload Excel", ss["SeksiJudul"]))
    keterangan = (
        "Catatan semua upload data Excel dari seluruh kelas &amp; guru."
        if is_superuser else
        "Catatan upload data Excel untuk kelas-kelas yang Anda ampu."
    )
    story.append(Paragraph(keterangan, ss["SeksiKeterangan"]))

    rows = []
    for r in (data.get("riwayat_upload") or []):
        nama_uploader = (
            r.diupload_oleh.first_name or r.diupload_oleh.username
            if r.diupload_oleh else "–"
        )
        if r.diupload_oleh and r.diupload_oleh.is_superuser:
            nama_uploader += " (Superuser)"
        rows.append([
            _p(r.nama_file, ss["Sel"]),
            _p(r.kelas.nama, ss["Sel"]),
            _p(nama_uploader, ss["Sel"]),
            _p(r.jumlah_siswa, ss["Sel"]),
            _p(_fmt_dt(r.diupload_pada), ss["Sel"]),
        ])
    story += _tabel_data(
        header=["File", "Kelas", "Diupload Oleh", "Siswa", "Waktu"],
        rows=rows,
        col_widths=[4.3 * cm, 2.7 * cm, 4 * cm, 1.7 * cm, 4.3 * cm],
        styles=ss,
        kosong_teks="Belum ada riwayat upload Excel.",
    )

    doc.build(
        story,
        onFirstPage=lambda c, d: _header_footer(c, d, "Riwayat Laporan"),
        onLaterPages=lambda c, d: _header_footer(c, d, "Riwayat Laporan"),
    )
    return buffer.getvalue()
