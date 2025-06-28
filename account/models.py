from django.db import models

# Create your models here.
'''CLIent Portal - CLIP'''

from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.conf import settings

from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

mobile_validator = RegexValidator(
    regex=r'^((\+92)|0)?3[0-9]{9}$',
    message="Enter a valid Pakistani mobile number (e.g. 03XXXXXXXXX or +923XXXXXXXXX)"
)

def validateforNumeric(number):
    if number.isdigit():
        raise ValidationError("This field cannot be only numbers.")

def validateUrl(url):
    urls=['https', 'http', 'www']
    if not any(x in url for x in urls) :
        return ('Please provide correct URL for your organization.')


class Organization(models.Model):
    name=models.CharField(max_length=30, validators=[validateforNumeric])
    location=models.CharField(max_length=30, validators=[validateforNumeric])
    url=models.URLField(validators=[validateforNumeric, validateUrl], blank=True, null=True)
    adminEmail=models.EmailField(validators=[validateforNumeric])
    user=models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    def __str__(self):
        return self.name


class Role(models.Model):
    role=models.CharField(max_length=30, unique=True)
    
    def __str__(self):
        return self.role
    

class Clients(models.Model):
    email=models.EmailField(unique=True)
    firstName=models.CharField(max_length=30, blank=True, null=True)
    lastName=models.CharField(max_length=30, blank=True, null=True)
    # ROLE_CHOICES=[
    #     ('teacher','Teacher'),
    #     ('student','Student')
    # ]
    role=models.ForeignKey(Role, on_delete=models.CASCADE)
    organization=models.ForeignKey(Organization, on_delete=models.CASCADE)
    user=models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.email