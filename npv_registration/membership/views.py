# membership/views.py
from rest_framework import status, generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.mail import EmailMessage
from django.conf import settings
from django.http import HttpResponse
from .models import Member
from .serializers import MemberSerializer, MemberListSerializer
from .certificate_generator import CertificateGenerator
import os


@api_view(['POST'])
def register_member(request):
    """
    Register a new member, generate certificate, and send email
    """
    serializer = MemberSerializer(data=request.data)

    if serializer.is_valid():
        try:
            # Save member
            member = serializer.save()

            # Generate certificate
            cert_generator = CertificateGenerator(member)
            pdf_buffer, qr_path = cert_generator.save_certificate()

            # Save certificate file
            cert_filename = f'certificate_{member.membership_number}.pdf'
            cert_path = os.path.join(settings.MEDIA_ROOT, 'certificates', cert_filename)

            os.makedirs(os.path.dirname(cert_path), exist_ok=True)
            with open(cert_path, 'wb') as f:
                f.write(pdf_buffer.read())

            member.certificate = f'certificates/{cert_filename}'
            member.qr_code = qr_path
            member.save()

            # Send email if email is provided
            if member.email:
                send_certificate_email(member, cert_path)

            return Response({
                'success': True,
                'message': 'Registration successful! Certificate has been generated.',
                'data': {
                    'membership_number': member.membership_number,
                    'full_name': member.get_full_name(),
                    'certificate_url': request.build_absolute_uri(member.certificate.url),
                    'email_sent': bool(member.email)
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            # If member was created but certificate generation failed, delete the member
            if 'member' in locals():
                member.delete()

            return Response({
                'success': False,
                'message': f'Registration failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({
        'success': False,
        'message': 'Validation failed',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


def send_certificate_email(member, cert_path):
    """Send certificate via email"""
    subject = f'NPV Membership Certificate - {member.membership_number}'

    message = f"""
    Dear {member.get_full_name()},

    Welcome to the National People's Voice Party!

    Your membership registration has been successfully completed.

    Membership Details:
    - Membership Number: {member.membership_number}
    - Category: {member.membership_category}
    - Registration Date: {member.registration_date.strftime('%B %d, %Y')}

    Please find your membership certificate attached to this email.

    You can verify your membership at any time by scanning the QR code on your certificate
    or visiting: https://npv.co.ke/verify/{member.membership_number}

    Thank you for joining us in building a better Kenya!

    "Our Voice, Our Strength"

    Best regards,
    National People's Voice Party

    ---
    Contact Us:
    Email: nationalpeoplesvoice@gmail.com
    Phone: +254-771-847-219
    Website: www.npv.co.ke
    """

    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[member.email],
    )

    # Attach certificate
    with open(cert_path, 'rb') as f:
        email.attach(
            f'NPV_Certificate_{member.membership_number}.pdf',
            f.read(),
            'application/pdf'
        )

    email.send(fail_silently=False)


@api_view(['GET'])
def verify_member(request, membership_number):
    """Verify membership by membership number"""
    try:
        member = Member.objects.get(membership_number=membership_number)
        return Response({
            'success': True,
            'verified': True,
            'data': {
                'full_name': member.get_full_name(),
                'membership_number': member.membership_number,
                'category': member.membership_category,
                'registration_date': member.registration_date.strftime('%B %d, %Y'),
                'county': member.county,
                'constituency': member.constituency
            }
        })
    except Member.DoesNotExist:
        return Response({
            'success': False,
            'verified': False,
            'message': 'Membership number not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def download_certificate(request, membership_number):
    """Download certificate PDF"""
    try:
        member = Member.objects.get(membership_number=membership_number)

        if not member.certificate:
            return Response({
                'success': False,
                'message': 'Certificate not found'
            }, status=status.HTTP_404_NOT_FOUND)

        cert_path = member.certificate.path

        with open(cert_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="NPV_Certificate_{membership_number}.pdf"'
            return response

    except Member.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Member not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MemberListView(generics.ListAPIView):
    """List all members"""
    queryset = Member.objects.all()
    serializer_class = MemberListSerializer


class MemberDetailView(generics.RetrieveAPIView):
    """Get member details"""
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    lookup_field = 'membership_number'