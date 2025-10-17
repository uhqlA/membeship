# membership/serializers.py
from rest_framework import serializers
from .models import Member
from datetime import date


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = '__all__'
        read_only_fields = ['membership_number', 'registration_date', 'certificate', 'qr_code']

    def validate_dob(self, value):
        """Validate date of birth - member must be at least 18 years old"""
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))

        if age < 18:
            raise serializers.ValidationError("Member must be at least 18 years old.")

        if age > 120:
            raise serializers.ValidationError("Invalid date of birth.")

        return value

    def validate_id_passport(self, value):
        """Validate ID/Passport number"""
        if not value or len(value.strip()) < 5:
            raise serializers.ValidationError("ID/Passport number must be at least 5 characters.")
        return value.strip()

    def validate_phone(self, value):
        """Validate phone number"""
        # Remove spaces and special characters
        cleaned = ''.join(filter(str.isdigit, value))
        if len(cleaned) < 9:
            raise serializers.ValidationError("Invalid phone number.")
        return value

    def validate_email(self, value):
        """Validate email if provided"""
        if value:
            # Check if email already exists
            if Member.objects.filter(email=value).exists():
                if not self.instance or self.instance.email != value:
                    raise serializers.ValidationError("This email is already registered.")
        return value


class MemberListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing members"""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = ['id', 'full_name', 'membership_number', 'membership_category',
                  'phone', 'email', 'registration_date']

    def get_full_name(self, obj):
        return obj.get_full_name()