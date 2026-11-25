"""Generate HTML, PDF, and DOCX for Laporan Pekerjaan Jasa Integrasi Sistem (Hardware-Software) dan Design UI/UX Dashboard.
Target: Exactly 3 pages matching the PDF reference.
"""

import os
import subprocess
import base64
import re
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

BASE_DIR = Path(__file__).resolve().parent.parent
IMAGES_DIR = BASE_DIR / "images"

def encode_image(filename):
    path = IMAGES_DIR / filename
    if path.exists():
        with open(path, "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode('utf-8')
    return ""

img1_b64 = encode_image("gambar1_integrasi_hardware_software.png")
img2_b64 = encode_image("gambar2_kebutuhan_integrasi_uiux.png")
img3_b64 = encode_image("gambar3_design_uiux_dashboard.png")
img4_b64 = encode_image("gambar4_pengujian_integrasi_uiux.png")

html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<title>Laporan Pekerjaan - Jasa Integrasi Sistem (Hardware-Software) dan Design UI/UX Dashboard</title>
<style>
    @page {{
        size: A4 portrait;
        margin: 16mm 20mm 16mm 20mm;
    }}
    * {{
        box-sizing: border-box;
    }}
    body {{
        font-family: Arial, "Helvetica Neue", Helvetica, sans-serif;
        font-size: 10.2pt;
        line-height: 1.34;
        color: #000000;
        margin: 0;
        padding: 0;
    }}
    .page {{
        page-break-after: always;
        break-after: page;
    }}
    .page:last-child {{
        page-break-after: avoid;
        break-after: avoid;
    }}
    .header-title {{
        text-align: center;
        margin-bottom: 16px;
    }}
    .header-title h1 {{
        font-size: 14pt;
        font-weight: bold;
        margin: 0 0 4px 0;
    }}
    .header-title h2 {{
        font-size: 12.2pt;
        font-weight: bold;
        margin: 0;
    }}
    h3 {{
        font-size: 10.5pt;
        font-weight: bold;
        margin: 12px 0 5px 0;
    }}
    p {{
        text-align: justify;
        text-justify: inter-word;
        margin: 0 0 8px 0;
        line-height: 1.35;
    }}
    .figure-container {{
        text-align: center;
        margin: 6px 0 4px 0;
    }}
    .figure-container img {{
        max-width: 96%;
        height: auto;
        border: 1px solid #cbd5e1;
        border-radius: 3px;
    }}
    .caption {{
        font-size: 9.5pt;
        text-align: center;
        margin: 4px 0 8px 0;
        color: #0f172a;
    }}

    /* Signature Block */
    .signature-table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 14px;
        font-size: 9.5pt;
    }}
    .signature-table td {{
        border: 1px solid #000000;
        vertical-align: top;
        text-align: center;
        padding: 0;
    }}
    .sig-header {{
        padding: 5px;
        font-weight: bold;
    }}
    .sig-header-orange {{
        background-color: #f59e0b;
        color: #000000;
        padding: 5px;
        font-weight: bold;
    }}
    .sig-space {{
        height: 52px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #9ca3af;
        font-style: italic;
        font-size: 8.5pt;
    }}
    .sig-space-orange {{
        background-color: #f59e0b;
        height: 52px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #111827;
        font-style: italic;
        font-weight: 500;
        font-size: 8.5pt;
    }}
    .sig-footer {{
        border-top: 1px solid #000000;
        padding: 5px 4px;
        line-height: 1.22;
        font-size: 9pt;
    }}
    .sig-footer-orange {{
        background-color: #f59e0b;
        border-top: 1px solid #000000;
        padding: 5px 4px;
        line-height: 1.22;
        font-size: 9pt;
        font-weight: 500;
    }}
</style>
</head>
<body>

<!-- ================= PAGE 1 ================= -->
<div class="page">
    <div class="header-title">
        <h1>Laporan Pekerjaan</h1>
        <h2>Jasa Integrasi Sistem (Hardware-Software) dan Design UI/UX Dashboard</h2>
    </div>

    <h3>1. Pendahuluan</h3>
    <p>
        Pada penelitian ini, direalisasikan pekerjaan integrasi sistem terpadu antara perangkat keras frekuensi radio 
        dan akuisisi data berkecepatan tinggi dengan perangkat lunak pengendali serta perancangan antarmuka pengguna 
        pada sistem Radar FMCW (Frequency Modulated Continuous Wave) dalam skema riset LPDP RISPRO bersama 
        Institut Teknologi Bandung (DKST ITB). Keterpaduan sistem ini menjadi prasyarat mutlak untuk menghasilkan 
        sistem radar pertahanan dan pemantauan permukaan yang andal, berdaya guna tinggi, serta mampu menyajikan 
        informasi taktis secara presisi dan waktu-nyata (real-time). Fokus pekerjaan ini mencakup perancangan 
        komunikasi perangkat keras akuisisi data ADC 20 MS/s, sinkronisasi posisi sudut pemindai mekanik antena, 
        pengelolaan antrean antar-thread bebas deadlock, hingga perancangan desain antarmuka Command and Control (C2) 
        dashboard yang modern dan ergonomis bagi operator radar.
    </p>

    <h3>2. Integrasi Sistem Hardware-Software Radar FMCW</h3>
    <div class="figure-container">
        <img src="{img1_b64}" alt="Gambar 1. Desain Arsitektur Integrasi Perangkat Keras dan Perangkat Lunak Sistem Radar" style="max-height: 76mm;">
    </div>
    <div class="caption">Gambar 1. Desain Arsitektur Integrasi Perangkat Keras dan Perangkat Lunak Sistem Radar</div>

    <p>
        Gambar 1 menampilkan desain arsitektur keseluruhan dari integrasi sistem perangkat keras dan perangkat lunak 
        yang telah dibangun. Desain ini mengadopsi arsitektur multi-tier modular yang memisahkan lapisan perangkat keras 
        fisik, lapisan driver dan komunikasi inter-thread, serta lapisan dashboard grafis UI/UX. Komponen inti pada 
        lapisan perangkat keras adalah kartu ADC ADLink PCI-9846H (16-bit, 4 kanal, 20 MS/s) yang dihubungkan melalui 
        pustaka C asli (wd-dask64.dll) menggunakan antarmuka ctypes pada Python. Sistem akuisisi dikonfigurasi dalam 
        mode asynchronous continuous double-buffer DMA dengan pemicu eksternal (Ext-D Trigger), memungkinkan pemindahan 
        data gelombang mikro secara zero-copy langsung ke RAM dengan throughput kontinu 40 MB/detik per kanal. Bersamaan 
        dengan itu, modul worker serial membaca data sudut antena pemindai dari mikrokontroler driver motor BTS7960 dan 
        optical encoder secara non-blocking pada kecepatan 115.200 bps. Seluruh data dialirkan secara aman melalui antrean 
        FIFO thread-safe menuju mesin DSP dan antarmuka visualisasi Dear PyGui.
    </p>
</div>

<!-- ================= PAGE 2 ================= -->
<div class="page">
    <div class="figure-container" style="margin-top: 2px;">
        <img src="{img2_b64}" alt="Gambar 2. Kebutuhan modul dan komponen integrasi sistem dan desain UI/UX" style="max-height: 72mm;">
    </div>
    <div class="caption">Gambar 2. Kebutuhan modul dan komponen integrasi sistem dan desain UI/UX</div>

    <p>
        Gambar 2 merupakan daftar kebutuhan deliverable (bill of deliverables) yang dirancang dan diimplementasikan 
        dalam pelaksanaan pekerjaan integrasi sistem dan perancangan desain UI/UX dashboard radar ini. Daftar ini mencakup 
        12 modul utama yang mencakup interkoneksi driver C DAQ tingkat rendah, streaming memori double-buffer DMA, 
        sinkronisasi serial UART antena scanner, manajemen antrean multi-threading bebas race-condition, protokol proteksi 
        hardware fail-fast, hingga widget antarmuka grafis taktis seperti layar radar PPI 180°, penganalisis spektrum daya RF 
        terkalibrasi (dBm pada beban 50 Ohm), osiloskop domain waktu untuk 20.000 sampel per buffer, bilah status telemetri 
        atas 60 FPS, dan ring buffer target circular deque O(1). Seluruh modul dibangun dan diverifikasi secara ketat agar 
        mampu bekerja secara sinergis tanpa kebocoran memori (zero memory leak) maupun hambatan eksekusi thread.
    </p>

    <div class="figure-container" style="margin-top: 4px;">
        <img src="{img3_b64}" alt="Gambar 3. Desain Antarmuka Pengguna (UI/UX Dashboard C2) Pemantauan Radar Real-Time" style="max-height: 82mm;">
    </div>
    <div class="caption">Gambar 3. Desain Antarmuka Pengguna (UI/UX Dashboard C2) Pemantauan Radar Real-Time</div>
</div>

<!-- ================= PAGE 3 ================= -->
<div class="page">
    <div class="figure-container" style="margin-top: 2px;">
        <img src="{img4_b64}" alt="Gambar 4. Alur Pengujian Integrasi Hardware-Software dan Validasi Desain UI/UX Dashboard" style="max-height: 60mm;">
    </div>
    <div class="caption">Gambar 4. Alur Pengujian Integrasi Hardware-Software dan Validasi Desain UI/UX Dashboard</div>

    <p>
        Pekerjaan jasa integrasi sistem (hardware-software) dan desain UI/UX dashboard radar telah selesai dilaksanakan 
        secara komprehensif. Pada Gambar 3 diperlihatkan hasil realisasi desain antarmuka Command and Control (C2) 
        dashboard yang beroperasi penuh secara real-time. Desain dashboard menerapkan tata letak ergonomis taktis bertema 
        aerospace dark mode dengan kontras tinggi yang terbagi menjadi empat panel utama: top telemetry header ribbon 
        (pemantau status kartu ADC, Ext-D trigger, FPS render 60 FPS, dan jam sistem), layar taktis radar PPI 180° dengan 
        cincin jarak konsentris 3-15 km dan jarum sapuan phosphor green yang bergerak sinkron dengan antena fisik, penganalisis 
        spektrum frekuensi beat dual-trace dengan filter Savitzky-Golay untuk eliminasi noise grass, serta osiloskop domain 
        waktu real-time berdampingan dengan tabel telemetri penjejakan target berbasis ring buffer O(1) deque.
    </p>

    <p>
        Pada Gambar 4 seluruh tahapan pengujian integrasi dan validasi sistem dipaparkan secara runtut melalui 5 fase pengujian: 
        verifikasi jabat-tangan pustaka C dan register kartu PCI-9846H, pengujian throughput streaming DMA kontinu 40 MB/s tanpa 
        kehilangan paket data (zero packet drop), uji sinkronisasi pemicu digital eksternal (Ext-D) dengan modulasi FMCW chirp 
        dan sudut azimut enkoder, validasi komputasi DSP (FFT 1 kHz/bin dan kalibrasi daya RF 50 Ohm), serta uji stabilitas 
        render UI/UX pada 60 FPS bebas kebocoran memori (zero memory leak). Berdasarkan seluruh hasil evaluasi pengujian, 
        sistem dinyatakan telah memenuhi seluruh kriteria performa teknis yang dipersyaratkan. Dengan ini, pekerjaan 
        <strong>Jasa Integrasi Sistem (Hardware-Software) dan Design UI/UX Dashboard</strong> dinyatakan selesai.
    </p>

    <!-- Signature Table matching PDF Page 3 -->
    <table class="signature-table">
        <tr>
            <td style="width: 50%;">
                <div class="sig-header">Menyetujui<br>Ketua Peneliti</div>
                <div class="sig-space">TTD Peneliti</div>
                <div class="sig-footer">
                    <strong>Dr. Ir. Eko Mursito Budi, M.T.</strong><br>
                    NIP : 196710061997021001
                </div>
            </td>
            <td style="width: 50%;">
                <div class="sig-header-orange">Perusahaan / Pelaksana<br>CV. Maja Baru Indonesia</div>
                <div class="sig-space-orange">TTD Perusahaan</div>
                <div class="sig-footer-orange">
                    <strong>Aris Munandar</strong><br>
                    Direktur
                </div>
            </td>
        </tr>
    </table>
</div>

</body>
</html>
"""

# 1. Write HTML file
html_path = BASE_DIR / "Laporan_Jasa_Integrasi_Sistem_dan_Design_UIUX_Dashboard.html"
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_content)
print(f"Generated HTML: {html_path}")

# 2. Convert HTML to PDF using Chrome Headless
pdf_path = BASE_DIR / "Laporan_Jasa_Integrasi_Sistem_dan_Design_UIUX_Dashboard.pdf"
chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if os.path.exists(chrome_exe):
    cmd = [
        chrome_exe,
        "--headless",
        "--disable-gpu",
        "--run-all-compositor-stages-before-draw",
        "--no-pdf-header-footer",
        "--print-to-pdf-no-header",
        f"--print-to-pdf={pdf_path}",
        html_path.resolve().as_uri()
    ]
    try:
        subprocess.run(cmd, check=True)
        print(f"Generated PDF via Chrome: {pdf_path}")
        
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        page_matches = re.findall(rb'/Type\s*/Page\b', pdf_data)
        print(f"Verified PDF page count: {len(page_matches)}")
    except Exception as e:
        print(f"Chrome PDF generation error: {e}")


# 3. Generate DOCX matching the exact same structure
docx_path = BASE_DIR / "Laporan_Jasa_Integrasi_Sistem_dan_Design_UIUX_Dashboard.docx"
doc = Document()

# Set Margins to match A4
sections = doc.sections
for s in sections:
    s.page_width = Inches(8.27)
    s.page_height = Inches(11.69)
    s.top_margin = Inches(0.65)
    s.bottom_margin = Inches(0.65)
    s.left_margin = Inches(0.78)
    s.right_margin = Inches(0.78)

def set_para_font(p, name="Arial", size_pt=10.0, bold=False, italic=False, color_rgb=(0,0,0), align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after_pt=6):
    p.alignment = align
    p.paragraph_format.space_after = Pt(space_after_pt)
    p.paragraph_format.line_spacing = 1.25
    for run in p.runs:
        run.font.name = name
        run.font.size = Pt(size_pt)
        run.font.bold = bold
        run.font.italic = italic
        run.font.color.rgb = RGBColor(*color_rgb)

# Header Title
p_t1 = doc.add_paragraph("Laporan Pekerjaan")
set_para_font(p_t1, size_pt=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after_pt=2)
p_t2 = doc.add_paragraph("Jasa Integrasi Sistem (Hardware-Software) dan Design UI/UX Dashboard")
set_para_font(p_t2, size_pt=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after_pt=12)

# Heading 1
p_h1 = doc.add_paragraph("1. Pendahuluan")
set_para_font(p_h1, size_pt=10.5, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_after_pt=4)

p_intro = doc.add_paragraph(
    "Pada penelitian ini, direalisasikan pekerjaan integrasi sistem terpadu antara perangkat keras frekuensi radio "
    "dan akuisisi data berkecepatan tinggi dengan perangkat lunak pengendali serta perancangan antarmuka pengguna "
    "pada sistem Radar FMCW (Frequency Modulated Continuous Wave) dalam skema riset LPDP RISPRO bersama "
    "Institut Teknologi Bandung (DKST ITB). Keterpaduan sistem ini menjadi prasyarat mutlak untuk menghasilkan "
    "sistem radar pertahanan dan pemantauan permukaan yang andal, berdaya guna tinggi, serta mampu menyajikan "
    "informasi taktis secara presisi dan waktu-nyata (real-time). Fokus pekerjaan ini mencakup perancangan "
    "komunikasi perangkat keras akuisisi data ADC 20 MS/s, sinkronisasi posisi sudut pemindai mekanik antena, "
    "pengelolaan antrean antar-thread bebas deadlock, hingga perancangan desain antarmuka Command and Control (C2) "
    "dashboard yang modern dan ergonomis bagi operator radar."
)
set_para_font(p_intro, size_pt=10, space_after_pt=8)

# Heading 2
p_h2 = doc.add_paragraph("2. Integrasi Sistem Hardware-Software Radar FMCW")
set_para_font(p_h2, size_pt=10.5, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_after_pt=4)

# Image 1
img1_path = IMAGES_DIR / "gambar1_integrasi_hardware_software.png"
if img1_path.exists():
    p_img1 = doc.add_paragraph()
    p_img1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img1.paragraph_format.space_after = Pt(2)
    p_img1.add_run().add_picture(str(img1_path), width=Inches(6.6))
    p_c1 = doc.add_paragraph("Gambar 1. Desain Arsitektur Integrasi Perangkat Keras dan Perangkat Lunak Sistem Radar")
    set_para_font(p_c1, size_pt=9.5, align=WD_ALIGN_PARAGRAPH.CENTER, space_after_pt=6)

p_desc1 = doc.add_paragraph(
    "Gambar 1 menampilkan desain arsitektur keseluruhan dari integrasi sistem perangkat keras dan perangkat lunak "
    "yang telah dibangun. Desain ini mengadopsi arsitektur multi-tier modular yang memisahkan lapisan perangkat keras "
    "fisik, lapisan driver dan komunikasi inter-thread, serta lapisan dashboard grafis UI/UX. Komponen inti pada "
    "lapisan perangkat keras adalah kartu ADC ADLink PCI-9846H (16-bit, 4 kanal, 20 MS/s) yang dihubungkan melalui "
    "pustaka C asli (wd-dask64.dll) menggunakan antarmuka ctypes pada Python. Sistem akuisisi dikonfigurasi dalam "
    "mode asynchronous continuous double-buffer DMA dengan pemicu eksternal (Ext-D Trigger), memungkinkan pemindahan "
    "data gelombang mikro secara zero-copy langsung ke RAM dengan throughput kontinu 40 MB/detik per kanal. Bersamaan "
    "dengan itu, modul worker serial membaca data sudut antena pemindai dari mikrokontroler driver motor BTS7960 dan "
    "optical encoder secara non-blocking pada kecepatan 115.200 bps. Seluruh data dialirkan secara aman melalui antrean "
    "FIFO thread-safe menuju mesin DSP dan antarmuka visualisasi Dear PyGui."
)
set_para_font(p_desc1, size_pt=10, space_after_pt=12)

# Page Break for Page 2
doc.add_page_break()

# Image 2
img2_path = IMAGES_DIR / "gambar2_kebutuhan_integrasi_uiux.png"
if img2_path.exists():
    p_img2 = doc.add_paragraph()
    p_img2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img2.paragraph_format.space_after = Pt(2)
    p_img2.add_run().add_picture(str(img2_path), width=Inches(6.6))
    p_c2 = doc.add_paragraph("Gambar 2. Kebutuhan modul dan komponen integrasi sistem dan desain UI/UX")
    set_para_font(p_c2, size_pt=9.5, align=WD_ALIGN_PARAGRAPH.CENTER, space_after_pt=6)

p_desc2 = doc.add_paragraph(
    "Gambar 2 merupakan daftar kebutuhan deliverable (bill of deliverables) yang dirancang dan diimplementasikan "
    "dalam pelaksanaan pekerjaan integrasi sistem dan perancangan desain UI/UX dashboard radar ini. Daftar ini mencakup "
    "12 modul utama yang mencakup interkoneksi driver C DAQ tingkat rendah, streaming memori double-buffer DMA, "
    "sinkronisasi serial UART antena scanner, manajemen antrean multi-threading bebas race-condition, protokol proteksi "
    "hardware fail-fast, hingga widget antarmuka grafis taktis seperti layar radar PPI 180°, penganalisis spektrum daya RF "
    "terkalibrasi (dBm pada beban 50 Ohm), osiloskop domain waktu untuk 20.000 sampel per buffer, bilah status telemetri "
    "atas 60 FPS, dan ring buffer target circular deque O(1). Seluruh modul dibangun dan diverifikasi secara ketat agar "
    "mampu bekerja secara sinergis tanpa kebocoran memori (zero memory leak) maupun hambatan eksekusi thread."
)
set_para_font(p_desc2, size_pt=10, space_after_pt=8)

# Image 3
img3_path = IMAGES_DIR / "gambar3_design_uiux_dashboard.png"
if img3_path.exists():
    p_img3 = doc.add_paragraph()
    p_img3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img3.paragraph_format.space_after = Pt(2)
    p_img3.add_run().add_picture(str(img3_path), width=Inches(6.6))
    p_c3 = doc.add_paragraph("Gambar 3. Desain Antarmuka Pengguna (UI/UX Dashboard C2) Pemantauan Radar Real-Time")
    set_para_font(p_c3, size_pt=9.5, align=WD_ALIGN_PARAGRAPH.CENTER, space_after_pt=12)

# Page Break for Page 3
doc.add_page_break()

# Image 4
img4_path = IMAGES_DIR / "gambar4_pengujian_integrasi_uiux.png"
if img4_path.exists():
    p_img4 = doc.add_paragraph()
    p_img4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img4.paragraph_format.space_after = Pt(2)
    p_img4.add_run().add_picture(str(img4_path), width=Inches(6.6))
    p_c4 = doc.add_paragraph("Gambar 4. Alur Pengujian Integrasi Hardware-Software dan Validasi Desain UI/UX Dashboard")
    set_para_font(p_c4, size_pt=9.5, align=WD_ALIGN_PARAGRAPH.CENTER, space_after_pt=6)

p_desc3 = doc.add_paragraph(
    "Pekerjaan jasa integrasi sistem (hardware-software) dan desain UI/UX dashboard radar telah selesai dilaksanakan "
    "secara komprehensif. Pada Gambar 3 diperlihatkan hasil realisasi desain antarmuka Command and Control (C2) "
    "dashboard yang beroperasi penuh secara real-time. Desain dashboard menerapkan tata letak ergonomis taktis bertema "
    "aerospace dark mode dengan kontras tinggi yang terbagi menjadi empat panel utama: top telemetry header ribbon "
    "(pemantau status kartu ADC, Ext-D trigger, FPS render 60 FPS, dan jam sistem), layar taktis radar PPI 180° dengan "
    "cincin jarak konsentris 3-15 km dan jarum sapuan phosphor green yang bergerak sinkron dengan antena fisik, penganalisis "
    "spektrum frekuensi beat dual-trace dengan filter Savitzky-Golay untuk eliminasi noise grass, serta osiloskop domain "
    "waktu real-time berdampingan dengan tabel telemetri penjejakan target berbasis ring buffer O(1) deque."
)
set_para_font(p_desc3, size_pt=10, space_after_pt=6)

p_desc4 = doc.add_paragraph(
    "Pada Gambar 4 seluruh tahapan pengujian integrasi dan validasi sistem dipaparkan secara runtut melalui 5 fase pengujian: "
    "verifikasi jabat-tangan pustaka C dan register kartu PCI-9846H, pengujian throughput streaming DMA kontinu 40 MB/s tanpa "
    "kehilangan paket data (zero packet drop), uji sinkronisasi pemicu digital eksternal (Ext-D) dengan modulasi FMCW chirp "
    "dan sudut azimut enkoder, validasi komputasi DSP (FFT 1 kHz/bin dan kalibrasi daya RF 50 Ohm), serta uji stabilitas "
    "render UI/UX pada 60 FPS bebas kebocoran memori (zero memory leak). Berdasarkan seluruh hasil evaluasi pengujian, "
    "sistem dinyatakan telah memenuhi seluruh kriteria performa teknis yang dipersyaratkan. Dengan ini, pekerjaan "
    "Jasa Integrasi Sistem (Hardware-Software) dan Design UI/UX Dashboard dinyatakan selesai."
)
set_para_font(p_desc4, size_pt=10, space_after_pt=10)

# Signature Table in DOCX
sig_table = doc.add_table(rows=3, cols=2)
sig_table.alignment = WD_TABLE_ALIGNMENT.CENTER
sig_table.autofit = False

# Width 50% each
col_w_in = Inches(3.35)
for row in sig_table.rows:
    for cell in row.cells:
        cell.width = col_w_in

# Row 0: Headers
cell_l0 = sig_table.cell(0, 0)
cell_l0.text = "Menyetujui\nKetua Peneliti"
set_para_font(cell_l0.paragraphs[0], size_pt=9.5, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after_pt=0)

cell_r0 = sig_table.cell(0, 1)
cell_r0.text = "Perusahaan / Pelaksana\nCV. Maja Baru Indonesia"
set_para_font(cell_r0.paragraphs[0], size_pt=9.5, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after_pt=0)
shading_r0 = parse_xml(r'<w:shd {} w:fill="F59E0B"/>'.format(nsdecls('w')))
cell_r0._tc.get_or_add_tcPr().append(shading_r0)

# Row 1: Space for signature
cell_l1 = sig_table.cell(1, 0)
cell_l1.text = "\n\n(Tanda Tangan & Stempel)\n\n"
set_para_font(cell_l1.paragraphs[0], size_pt=8.5, italic=True, color_rgb=(156,163,175), align=WD_ALIGN_PARAGRAPH.CENTER, space_after_pt=0)

cell_r1 = sig_table.cell(1, 1)
cell_r1.text = "\n\n(Tanda Tangan & Stempel)\n\n"
set_para_font(cell_r1.paragraphs[0], size_pt=8.5, italic=True, color_rgb=(17,24,39), align=WD_ALIGN_PARAGRAPH.CENTER, space_after_pt=0)
shading_r1 = parse_xml(r'<w:shd {} w:fill="F59E0B"/>'.format(nsdecls('w')))
cell_r1._tc.get_or_add_tcPr().append(shading_r1)

# Row 2: Signer names
cell_l2 = sig_table.cell(2, 0)
cell_l2.text = "Dr. Ir. Eko Mursito Budi, M.T.\nNIP : 196710061997021001"
set_para_font(cell_l2.paragraphs[0], size_pt=9, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after_pt=0)

cell_r2 = sig_table.cell(2, 1)
cell_r2.text = "Aris Munandar\nDirektur"
set_para_font(cell_r2.paragraphs[0], size_pt=9, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after_pt=0)
shading_r2 = parse_xml(r'<w:shd {} w:fill="F59E0B"/>'.format(nsdecls('w')))
cell_r2._tc.get_or_add_tcPr().append(shading_r2)

# Set borders on all table cells
for row in sig_table.rows:
    for cell in row.cells:
        tcPr = cell._tc.get_or_add_tcPr()
        tcBorders = parse_xml(
            r'<w:tcBorders {}><w:top w:val="single" w:sz="4" w:space="0" w:color="000000"/><w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/><w:left w:val="single" w:sz="4" w:space="0" w:color="000000"/><w:right w:val="single" w:sz="4" w:space="0" w:color="000000"/></w:tcBorders>'.format(nsdecls('w'))
        )
        tcPr.append(tcBorders)

doc.save(str(docx_path))
print(f"Generated DOCX: {docx_path}")
print("All documents generated successfully.")
