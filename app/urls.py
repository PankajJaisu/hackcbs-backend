
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from app import views

urlpatterns = [
path('generate-otp/',views.generate_otp),
path('verify-otp/',views.verify_otp),
path('user-registration/',views.user_registration),
path('generate-card/',views.generate_card),
path('upload-prescription/',views.upload_prescription),

]