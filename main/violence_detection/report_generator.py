import os
import sqlite3
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm

class ReportGenerator:
    def __init__(self, db_path, report_path):
        self.db_path = db_path
        self.report_path = report_path
        self.last_report_path = None
        os.makedirs(self.report_path, exist_ok=True)
        self._register_fonts()

    def _register_fonts(self):
        font_path = os.path.join(os.path.dirname(__file__), "DejaVuSans.ttf")
        if not os.path.exists(font_path):
            raise FileNotFoundError("DejaVuSans.ttf dosyası bulunamadı. Lütfen dosya dizinine ekleyin.")
        pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))

    def generate(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, timestamp, label, confidence, screenshot_path, fps, latency FROM events WHERE label = 'Violence'")
                events = cursor.fetchall()

            if not events:
                self.last_report_path = None
                return {
                    "success": False,
                    "reason": "no_events",
                    "message": "Rapor için kayıtlı şiddet olayı yok.",
                    "path": None,
                    "event_count": 0,
                    "last_report_path": None,
                }

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = os.path.join(self.report_path, f"violence_report_{timestamp}.pdf")
            self.last_report_path = report_file
            event_count = len(events)
            doc = SimpleDocTemplate(
                report_file,
                pagesize=A4,
                rightMargin=15*mm,
                leftMargin=15*mm,
                topMargin=15*mm,
                bottomMargin=15*mm,
                title="Canlı Kavga Tespiti ve Raporlanması Projesi Raporu",
                author="Berkant Şimşek, Ömer Avcı - İstanbul Topkapı Üniversitesi",
                creator="Canlı Kavga Tespiti ve Raporlanması Projesi"
            )
            elements = []

            # Stil ayarları
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(
                name='Footer',
                fontName='DejaVuSans',
                fontSize=8,
                textColor=colors.grey,
                alignment=1  # Ortala
            ))
            styles.add(ParagraphStyle(
                name='Team',
                fontName='DejaVuSans',
                fontSize=10,
                leading=14,
                spaceBefore=12
            ))
            styles["Title"].fontName = "DejaVuSans"
            styles["Title"].fontSize = 20
            styles["Title"].spaceAfter = 12
            styles["Normal"].fontName = "DejaVuSans"
            styles["Normal"].fontSize = 10
            styles["Heading2"].fontName = "DejaVuSans"
            styles["Heading2"].fontSize = 14
            styles["Heading2"].spaceAfter = 10

            # Başlık ve logo
            logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=120, height=60)
                logo.hAlign = 'LEFT'
                elements.append(logo)
            elements.append(Paragraph("Canlı Kavga Tespiti ve Raporlanması Projesi Raporu", styles["Title"]))
            elements.append(Paragraph(
                f"Rapor Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                styles["Normal"]
            ))
            elements.append(Paragraph("Proje: Canlı Kavga Tespiti ve Raporlanması Projesi", styles["Normal"]))
            elements.append(Paragraph("Kapsam: İstanbul Topkapı Üniversitesi Bitirme Projesi", styles["Normal"]))
            elements.append(Paragraph("Hazırlayanlar: Berkant Şimşek ve Ömer Avcı", styles["Normal"]))
            elements.append(Spacer(1, 12))

            # Özet bilgileri
            confidences = []
            timestamps = []
            for event in events:
                confidence = event[3]
                try:
                    confidence = float(confidence) if confidence is not None else 0.0
                    confidences.append(confidence)
                except (ValueError, TypeError):
                    confidences.append(0.0)
                timestamps.append(event[1])
            avg_confidence = sum(confidences) / event_count if event_count > 0 else 0.0
            min_confidence = min(confidences) if confidences else 0.0
            max_confidence = max(confidences) if confidences else 0.0
            date_range = f"{min(timestamps)} - {max(timestamps)}" if timestamps else "-"

            elements.append(Paragraph("Rapor Özeti", styles["Heading2"]))
            summary_data = [
                ["Toplam Olay Sayısı", str(event_count)],
                ["Ortalama Güven", f"{avg_confidence:.2f}"],
                ["Minimum Güven", f"{min_confidence:.2f}"],
                ["Maksimum Güven", f"{max_confidence:.2f}"],
                ["Tarih Aralığı", date_range]
            ]
            summary_table = Table(summary_data, colWidths=[100*mm, 80*mm])
            summary_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8ECEF')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(summary_table)
            elements.append(Spacer(1, 12))

            # Olay tablosu
            elements.append(Paragraph("Olay Detayları", styles["Heading2"]))
            data = [["ID", "Zaman", "Etiket", "Güven", "FPS", "Gecikme (s)"]]
            for event in events:
                id, timestamp, label, confidence, screenshot_path, fps, latency = event
                timestamp = timestamp.decode('utf-8') if isinstance(timestamp, bytes) else str(timestamp)
                label = label.decode('utf-8') if isinstance(label, bytes) else str(label)
                try:
                    if isinstance(confidence, bytes):
                        confidence = float(confidence.decode('utf-8'))
                    else:
                        confidence = float(confidence) if confidence is not None else 0.0
                except (ValueError, TypeError) as e:
                    print(f"Confidence dönüşüm hatası: {confidence}, hata: {e}")
                    confidence = 0.0
                fps = float(fps) if fps is not None else 0.0
                latency = float(latency) if latency is not None else 0.0
                # Güven için renk kodlaması
                confidence_text = Paragraph(f"{confidence:.2f}", ParagraphStyle(
                    name='Confidence',
                    fontName='DejaVuSans',
                    fontSize=9,
                    textColor=colors.green if confidence > 0.8 else colors.red if confidence < 0.6 else colors.black
                ))
                data.append([str(id), timestamp, label, confidence_text, f"{fps:.1f}", f"{latency:.3f}"])

            table = Table(data, colWidths=[20*mm, 50*mm, 30*mm, 30*mm, 25*mm, 35*mm])
            table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#40C4FF')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F9FAFB')),
                ('BACKGROUND', (0, 2), (-1, -2), colors.HexColor('#E8ECEF')),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 12))

            # Ekran görüntüleri
            elements.append(Paragraph("Olay Ekran Görüntüleri", styles["Heading2"]))
            for event in events:
                id, timestamp, label, confidence, screenshot_path, fps, latency = event
                timestamp = timestamp.decode('utf-8') if isinstance(timestamp, bytes) else str(timestamp)
                screenshot_path = screenshot_path.decode('utf-8') if isinstance(screenshot_path, bytes) else str(screenshot_path)
                try:
                    confidence = float(confidence) if confidence is not None else 0.0
                except (ValueError, TypeError) as e:
                    print(f"Confidence dönüşüm hatası (görüntü): {confidence}, hata: {e}")
                    confidence = 0.0
                if os.path.exists(screenshot_path):
                    elements.append(Paragraph(f"Olay #{id}: {timestamp}, Güven: {confidence:.2f}", styles["Normal"]))
                    img = Image(screenshot_path, width=250, height=180)
                    img.hAlign = 'CENTER'
                    elements.append(img)
                    elements.append(Spacer(1, 12))
                else:
                    elements.append(Paragraph(f"Görüntü bulunamadı: {screenshot_path}", styles["Normal"]))
                    print(f"Ekran görüntüsü eksik: {screenshot_path}")

            # Proje bilgisi
            elements.append(Paragraph("Proje Bilgisi", styles["Heading2"]))
            elements.append(Paragraph(
                "Bu rapor, İstanbul Topkapı Üniversitesi bitirme projesi kapsamında hazırlanan "
                "Canlı Kavga Tespiti ve Raporlanması Projesi için oluşturulmuştur.<br/>"
                "Hazırlayanlar: Berkant Şimşek ve Ömer Avcı",
                styles["Team"]
            ))

            # PDF oluştur
            def add_page_numbers(canvas, doc):
                page_num = canvas.getPageNumber()
                canvas.setFont("DejaVuSans", 8)
                canvas.setFillColor(colors.grey)
                canvas.drawString(15*mm, 10*mm, "İstanbul Topkapı Üniversitesi Bitirme Projesi")
                canvas.drawString(180*mm, 10*mm, f"Sayfa {page_num}")

            doc.build(elements, onFirstPage=add_page_numbers, onLaterPages=add_page_numbers)
            return {
                "success": True,
                "reason": "created",
                "message": f"Rapor oluşturuldu: {report_file}",
                "path": report_file,
                "event_count": event_count,
                "last_report_path": self.last_report_path,
            }
        except Exception as e:
            print(f"Rapor hatası: {e}")
            self.last_report_path = None
            return {
                "success": False,
                "reason": "error",
                "message": "Rapor oluşturulamadı. Ayrıntılar terminalde.",
                "path": None,
                "event_count": 0,
                "last_report_path": None,
                "error": str(e),
            }
