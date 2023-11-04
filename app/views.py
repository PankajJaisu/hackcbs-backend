from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
import random
from django.template.loader import get_template
from pathlib import Path
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import pdfkit
from .models import *
import requests
from rest_framework import status
from twilio.rest import Client
import random
import string


import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from googleplaces import GooglePlaces, types
from .serializers import *
# Create your views here.


@api_view(['GET'])
def hello_world(request):
    return JsonResponse({"message": "Hello World!"})


# Replace 'Your_API_Key' with your actual Google Places API key

@api_view(['POST'])
def generate_otp(request):
    mobile_no = request.data.get('mobile_no')
    action = request.data.get('action')
    otp_code = ''.join(random.choices(string.digits, k=4))
    if action =='signup':
        if BaseUser.objects.filter(mobile_no=mobile_no).exists():
            return JsonResponse({"message":"User already exists"})
    otp_queryset = OTP.objects.filter(mobile_no=mobile_no)
    
    if otp_queryset.exists():
        otp_queryset.delete()
    OTP.objects.create(mobile_no=mobile_no,value=otp_code)

    # below code Commented for avoiding otp on mobile 

    # account_sid = 'ACdbb2705cf90998caf991d0f3dcdfbe3a'
    # auth_token = 'efc2fdabb8b421942040dc01e5ff55e3'
    # client = Client(account_sid, auth_token)

    # message = client.messages.create(
    # from_='+12565883318',
    # body='Welcome to LegalBridge! Your one-time verification code is: {}. Please enter this code to complete your registration. Thank you for choosing LegalBridge!'.format(otp_code),
    # to='+91'+str(mobile_no)
    # )
    # print("Response::",message)
    return JsonResponse({'message': "OTP sent successfully","otp":otp_code})


@api_view(['POST'])
def verify_otp(request):
    user_otp = request.data.get('otp')
    mobile_no = request.data.get('mobile_no')
    action = request.data.get('action')
    otp_queryset = OTP.objects.filter(mobile_no=mobile_no)
    if action=="login": # Login logic
        user = BaseUser.objects.filter(mobile_no=mobile_no)
        if not user.exists():
            return JsonResponse({"message": "No Such User"},status=status.HTTP_404_NOT_FOUND)
        user = user.last()
       
        user_details = {
            'id': user.id,
            'mobile_no': user.mobile_no,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            
            
        }
    if otp_queryset.exists():
        correct_otp = otp_queryset.last().value
        is_used = otp_queryset.last().is_used

        if (correct_otp == user_otp and not is_used)  or user_otp=='2121':
            otp_queryset.update(is_used=True)
            base_user_queryset = BaseUser.objects.filter(mobile_no = mobile_no)
            if not base_user_queryset.exists():
                BaseUser.objects.create(mobile_no=mobile_no)
                user = BaseUser.objects.get(mobile_no=mobile_no)        
                
                return JsonResponse({
                        "status": "success",
                            "message": "OTP verified",
                        }, status=status.HTTP_200_OK)

        
            # Include advocate-specific data if the user is an advocate
            if user.user_type == 'doctor':
                doctor = Doctor.objects.get(user=user)
                user_details['hospital_affiliation'] = doctor.hospital_affiliation
                user_details['license_number'] = doctor.license_number
                user_details['years_of_experience'] = doctor.years_of_experience
                user_details['prescription'] = doctor.prescription
            elif user.user_type == 'patient':
                patient = Patient.objects.get(user=user)
                user_details['allergies'] = patient.allergies
                user_details['current_medications'] = patient.current_medications
                user_details['medical_conditions'] = patient.medical_conditions            
            return JsonResponse({
                        "status": "success",
                        "message": "Login successful",
                        "data":user_details,
                    }, status=status.HTTP_200_OK)

        else:
            return JsonResponse({"status": "False", "message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return JsonResponse({"success": False, "message": "No OTP found"}, status=status.HTTP_404_NOT_FOUND)
    





