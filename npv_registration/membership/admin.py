from django.contrib import admin

# Register your models here.
# membership/admin.py
from django.contrib import admin
from .models import Member, MembershipCounter


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['membership_number', 'get_full_name', 'membership_category',
                    'phone', 'email', 'county', 'registration_date']
    list_filter = ['membership_category', 'gender', 'special_interest', 'county', 'registration_date']
    search_fields = ['surname', 'other_names', 'membership_number', 'id_passport', 'phone', 'email']
    readonly_fields = ['membership_number', 'registration_date', 'certificate', 'qr_code']

    fieldsets = (
        ('Personal Information', {
            'fields': ('surname', 'other_names', 'id_passport', 'phone', 'email',
                       'gender', 'dob', 'ethnicity', 'religion', 'special_interest')
        }),
        ('Location Information', {
            'fields': ('county', 'constituency', 'ward', 'polling_station',
                       'diaspora', 'embassy')
        }),
        ('Membership Information', {
            'fields': ('membership_category', 'membership_number', 'registration_date')
        }),
        ('Certificate & QR Code', {
            'fields': ('certificate', 'qr_code')
        }),
    )

    def get_full_name(self, obj):
        return obj.get_full_name()

    get_full_name.short_description = 'Full Name'

    actions = ['regenerate_certificates']

    def regenerate_certificates(self, request, queryset):
        from .certificate_generator import CertificateGenerator
        import os
        from django.conf import settings

        for member in queryset:
            try:
                cert_generator = CertificateGenerator(member)
                pdf_buffer, qr_path = cert_generator.save_certificate()

                cert_filename = f'certificate_{member.membership_number}.pdf'
                cert_path = os.path.join(settings.MEDIA_ROOT, 'certificates', cert_filename)

                os.makedirs(os.path.dirname(cert_path), exist_ok=True)
                with open(cert_path, 'wb') as f:
                    f.write(pdf_buffer.read())

                member.certificate = f'certificates/{cert_filename}'
                member.qr_code = qr_path
                member.save()

            except Exception as e:
                self.message_user(request, f'Error for {member.membership_number}: {str(e)}', level='error')

        self.message_user(request, f'Successfully regenerated certificates for {queryset.count()} members.')

    regenerate_certificates.short_description = 'Regenerate certificates for selected members'


@admin.register(MembershipCounter)
class MembershipCounterAdmin(admin.ModelAdmin):
    list_display = ['category', 'last_number']
    readonly_fields = ['category', 'last_number']