from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from weasyprint import HTML

from certificates.models import Certificate


def generate_certificate_pdf(certificate):
    enrollment = certificate.enrollment
    student = enrollment.user
    course = enrollment.course

    html = render_to_string(
        "certificates/certificate.html",
        {"certificate": certificate, "student": student, "course": course},
    )
    pdf = HTML(string=html).write_pdf()

    return pdf


def generate_certificate_number():
    import uuid

    return f"CERT_{uuid.uuid4().hex[:12].upper()}"


def create_certificate(enrollment):
    certificate = Certificate.objects.create(
        enrollment=enrollment, certificate_number=generate_certificate_number()
    )
    pdf = generate_certificate_pdf(certificate)
    certificate.file.save(
        f"{certificate.certificate_number}.pdf", ContentFile(pdf), save=True
    )

    return certificate
