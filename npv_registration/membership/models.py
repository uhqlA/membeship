# membership/models.py
from django.db import models
from django.core.validators import RegexValidator
from datetime import datetime


class Member(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    SPECIAL_INTEREST_CHOICES = [
        ('None', 'None'),
        ('Youth', 'Youth'),
        ('Women', 'Women'),
        ('PWD', 'PWD'),
    ]

    MEMBERSHIP_CATEGORY_CHOICES = [
        ('Ordinary Membership', 'Ordinary Membership'),
        ('Bronze Membership', 'Bronze Membership'),
        ('Life Membership', 'Life Membership'),
        ('Associate Membership', 'Associate Membership'),
        ('Group Membership', 'Group Membership'),
        ('Honorary Membership', 'Honorary Membership'),
    ]

    # Personal Information
    surname = models.CharField(max_length=100)
    other_names = models.CharField(max_length=200)
    id_passport = models.CharField(max_length=50, unique=True)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$')
    phone = models.CharField(validators=[phone_regex], max_length=17)
    email = models.EmailField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    ethnicity = models.CharField(max_length=100, blank=True, null=True)
    religion = models.CharField(max_length=100, blank=True, null=True)
    dob = models.DateField()
    special_interest = models.CharField(max_length=20, choices=SPECIAL_INTEREST_CHOICES)

    # Location Information
    county = models.CharField(max_length=100)
    constituency = models.CharField(max_length=100)
    ward = models.CharField(max_length=100, blank=True, null=True)
    polling_station = models.CharField(max_length=200, blank=True, null=True)
    diaspora = models.CharField(max_length=100, blank=True, null=True)
    embassy = models.CharField(max_length=100, blank=True, null=True)

    # Membership Information
    membership_category = models.CharField(max_length=50, choices=MEMBERSHIP_CATEGORY_CHOICES)
    membership_number = models.CharField(max_length=20, unique=True, blank=True)
    registration_date = models.DateTimeField(auto_now_add=True)

    # Certificate
    certificate = models.FileField(upload_to='certificates/', blank=True, null=True)
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)

    class Meta:
        ordering = ['-registration_date']
        verbose_name = 'Member'
        verbose_name_plural = 'Members'

    def __str__(self):
        return f"{self.surname} {self.other_names} - {self.membership_number}"

    def get_full_name(self):
        return f"{self.surname} {self.other_names}"

    def save(self, *args, **kwargs):
        if not self.membership_number:
            self.membership_number = self.generate_membership_number()
        super().save(*args, **kwargs)

    def generate_membership_number(self):
        """Generate membership number based on category"""
        category_map = {
            'Ordinary Membership': 'OM',
            'Bronze Membership': 'BM',
            'Life Membership': 'LM',
            'Associate Membership': 'AM',
            'Group Membership': 'GM',
            'Honorary Membership': 'HM',
        }

        prefix = f"NPV/{category_map.get(self.membership_category, 'OM')}"

        # Get the last member with this category
        last_member = Member.objects.filter(
            membership_number__startswith=prefix
        ).order_by('-membership_number').first()

        if last_member and last_member.membership_number:
            try:
                last_number = int(last_member.membership_number.split('-')[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1

        return f"{prefix}-{new_number:03d}"


class MembershipCounter(models.Model):
    """Track membership numbers for each category"""
    category = models.CharField(max_length=50, unique=True)
    last_number = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.category}: {self.last_number}"