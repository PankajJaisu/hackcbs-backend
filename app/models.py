from django.db import models

# Create your models here.
from django.db import models

class BaseUser(models.Model):
    USER_TYPES = (
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
      
    )
   
    mobile_no = models.CharField(max_length=12,unique=True)
    user_type = models.CharField(max_length=15, choices=USER_TYPES)
    first_name = models.CharField(max_length=30,null=True, blank=True)
    last_name = models.CharField(max_length=30,null=True,blank=True)
    email = models.CharField(max_length=30,null=True, blank=True)
    profile_picture = models.ImageField(upload_to='uploads/',null=True, blank=True)
    profile_picture_url = models.CharField(max_length=300,null=True, blank=True)
class Doctor(models.Model):
    user = models.OneToOneField(BaseUser, on_delete=models.CASCADE)
    hospital_affiliation = models.CharField(max_length=100,null=True, blank=True)
    license_number = models.CharField(max_length=50,null=True, blank=True)
    years_of_experience = models.PositiveIntegerField(null=True, blank=True)
    letter_head_url = models.CharField(max_length=400,null=True, blank=True)       
    
class Patient(models.Model):
    user = models.OneToOneField(BaseUser, on_delete=models.CASCADE)
    allergies = models.TextField(null=True, blank=True)
    current_medications = models.TextField(null=True, blank=True)
    medical_conditions = models.TextField(null=True, blank=True)
    prescription_url = models.CharField(max_length=400,null=True, blank=True)       
    
class Document(models.Model):
    
    user = models.ForeignKey(BaseUser, on_delete=models.CASCADE,null=True, blank=True)
    file_name = models.CharField(max_length=100,null=True, blank=True)
    hash_value = models.CharField(max_length=300,null=True, blank=True)
    download_image = models.ImageField(upload_to='uploads/',null=True, blank=True)
    download_image_url = models.CharField(max_length=300,null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True,)
    updated_at = models.DateTimeField(auto_now=True)

    
class OTP(models.Model):
   
    user = models.ForeignKey(BaseUser, on_delete=models.CASCADE,null=True,blank=True)
    mobile_no = models.CharField(max_length=12,null=True,blank=True)
    value = models.CharField(max_length=10,null=True, blank=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
