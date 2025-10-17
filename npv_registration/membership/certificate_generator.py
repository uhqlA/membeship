# membership/certificate_generator.py
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, black, gold
from reportlab.lib.utils import ImageReader
import qrcode
from io import BytesIO
from datetime import datetime
import os
from django.conf import settings


class CertificateGenerator:
    def __init__(self, member):
        self.member = member
        self.width, self.height = landscape(A4)

    def generate_qr_code(self):
        """Generate QR code for verification"""
        verification_url = f"https://npv.co.ke/verify/{self.member.membership_number}"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(verification_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Save to BytesIO
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        return buffer

    def create_certificate(self):
        """Create the membership certificate PDF"""
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=landscape(A4))

        # Colors
        gold_color = HexColor('#FFD700')
        dark_blue = HexColor('#003366')

        # Draw border
        c.setStrokeColor(gold_color)
        c.setLineWidth(3)
        c.rect(0.5 * inch, 0.5 * inch, self.width - 1 * inch, self.height - 1 * inch)

        c.setLineWidth(1)
        c.rect(0.6 * inch, 0.6 * inch, self.width - 1.2 * inch, self.height - 1.2 * inch)

        # Title
        c.setFont("Helvetica-Bold", 32)
        c.setFillColor(dark_blue)
        c.drawCentredString(self.width / 2, self.height - 1.5 * inch,
                            "NATIONAL PEOPLE'S VOICE")

        c.setFont("Helvetica", 18)
        c.drawCentredString(self.width / 2, self.height - 1.9 * inch,
                            '"Our Voice, Our Strength"')

        # Certificate of Membership
        c.setFont("Helvetica-Bold", 24)
        c.setFillColor(gold_color)
        c.drawCentredString(self.width / 2, self.height - 2.6 * inch,
                            "CERTIFICATE OF MEMBERSHIP")

        # Decorative line
        c.setStrokeColor(gold_color)
        c.setLineWidth(2)
        c.line(self.width / 2 - 3 * inch, self.height - 2.8 * inch,
               self.width / 2 + 3 * inch, self.height - 2.8 * inch)

        # This certifies that
        c.setFont("Helvetica", 14)
        c.setFillColor(black)
        c.drawCentredString(self.width / 2, self.height - 3.3 * inch,
                            "This is to certify that")

        # Member Name
        c.setFont("Helvetica-Bold", 28)
        c.setFillColor(dark_blue)
        full_name = self.member.get_full_name().upper()
        c.drawCentredString(self.width / 2, self.height - 3.9 * inch, full_name)

        # Underline name
        c.setStrokeColor(gold_color)
        c.setLineWidth(1)
        name_width = c.stringWidth(full_name, "Helvetica-Bold", 28)
        c.line(self.width / 2 - name_width / 2, self.height - 4 * inch,
               self.width / 2 + name_width / 2, self.height - 4 * inch)

        # Membership details
        c.setFont("Helvetica", 12)
        c.setFillColor(black)

        details_y = self.height - 4.5 * inch
        c.drawCentredString(self.width / 2, details_y,
                            f"is a registered member of the National People's Voice Party")

        c.drawCentredString(self.width / 2, details_y - 0.3 * inch,
                            f"under {self.member.membership_category}")

        # Membership Number
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(dark_blue)
        c.drawCentredString(self.width / 2, details_y - 0.7 * inch,
                            f"Membership Number: {self.member.membership_number}")

        # Date
        c.setFont("Helvetica", 11)
        c.setFillColor(black)
        reg_date = self.member.registration_date.strftime("%B %d, %Y")
        c.drawCentredString(self.width / 2, details_y - 1.1 * inch,
                            f"Registration Date: {reg_date}")

        # Location info
        location = f"{self.member.ward}, {self.member.constituency}, {self.member.county}"
        c.drawCentredString(self.width / 2, details_y - 1.4 * inch,
                            f"Location: {location}")

        # Generate and add QR code
        qr_buffer = self.generate_qr_code()
        qr_image = ImageReader(qr_buffer)
        qr_size = 1.2 * inch
        c.drawImage(qr_image, 1 * inch, 1 * inch, qr_size, qr_size)

        # QR Code label
        c.setFont("Helvetica", 8)
        c.drawCentredString(1 * inch + qr_size / 2, 0.8 * inch,
                            "Scan to Verify")

        # Signature section
        sig_y = 1.5 * inch

        # Left signature
        c.setFont("Helvetica", 10)
        c.line(self.width - 5 * inch, sig_y, self.width - 3 * inch, sig_y)
        c.drawCentredString(self.width - 4 * inch, sig_y - 0.2 * inch,
                            "Party Leader")

        # Right signature
        c.line(self.width - 2.5 * inch, sig_y, self.width - 0.5 * inch, sig_y)
        c.drawCentredString(self.width - 1.5 * inch, sig_y - 0.2 * inch,
                            "Secretary General")

        # Footer
        c.setFont("Helvetica", 8)
        c.setFillColor(HexColor('#666666'))
        c.drawCentredString(self.width / 2, 0.7 * inch,
                            "National People's Voice Party | www.npv.co.ke | nationalpeoplesvoice@gmail.com")

        c.showPage()
        c.save()

        buffer.seek(0)
        return buffer

    def save_certificate(self):
        """Generate and save certificate"""
        pdf_buffer = self.create_certificate()

        # Save QR code
        qr_buffer = self.generate_qr_code()
        qr_filename = f'qrcode_{self.member.membership_number}.png'
        qr_path = os.path.join(settings.MEDIA_ROOT, 'qrcodes', qr_filename)

        os.makedirs(os.path.dirname(qr_path), exist_ok=True)
        with open(qr_path, 'wb') as f:
            f.write(qr_buffer.read())

        return pdf_buffer, f'qrcodes/{qr_filename}'