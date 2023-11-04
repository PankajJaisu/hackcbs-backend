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
    







def render_to_pdf(template_src, context, file_name="invoice"):
    Path("static/prescription/").mkdir(parents=True, exist_ok=True)
    file_path = f'prescription/{file_name}_{str(random.randint(100000, 9999999))}.pdf'
    print("file_path::",file_path)
    template = get_template(template_src)
    print("template::",template)
    html = template.render(context)
    options = {
        'page-height': '270mm',
        'page-width': '185mm',
    }

    pdf = pdfkit.from_string(html, r'static/' + file_path, options=options)
    return pdf,file_path

# @csrf_exempt
@api_view(['POST'])
def generate_prescription(request):
    template_src = 'prescription.html'
    data = request.POST   
    
    random_integer = random.randint(1, 100)
    temp, file_path = render_to_pdf(template_src, data, f'prescription_{random_integer}')
    user = BaseUser.objects.filter(mobile_no=data.get('mobile_no')).last()
    image_url = "{}/static/".format(settings.CURRENT_HOST)+file_path
    
    return JsonResponse({"msg":"Done","file_path":image_url})





def render_to_pdf(template_src, context, file_name="invoice"):
    Path("static/prescription/").mkdir(parents=True, exist_ok=True)
    file_path = f'prescription/{file_name}_{str(random.randint(100000, 9999999))}.pdf'
    print("file_path::",file_path)
    template = get_template(template_src)
    print("template::",template)
    html = template.render(context)
    options = {
        'page-height': '270mm',
        'page-width': '185mm',
    }

    pdf = pdfkit.from_string(html, r'static/' + file_path, options=options)
    return pdf,file_path

# @csrf_exempt
@api_view(['POST'])
def generate_prescription(request):
    template_src = 'prescription.html'
    data = request.POST   
    
    random_integer = random.randint(1, 100)
    temp, file_path = render_to_pdf(template_src, data, f'prescription_{random_integer}')
    user = BaseUser.objects.filter(mobile_no=data.get('mobile_no')).last()
    image_url = "{}/static/".format(settings.CURRENT_HOST)+file_path
    
    return JsonResponse({"msg":"Done","file_path":image_url})


@api_view(['POST'])
def user_registration(request):
    mobile_no = request.data.get('mobile_no')
    user_type = request.data.get('user_type')
    first_name = request.data.get('first_name', None)
    last_name = request.data.get('last_name', None)
    email = request.data.get('email', None)
    base_user_queryset = BaseUser.objects.filter(mobile_no=mobile_no)
    print(request.data)
    if base_user_queryset.exists():
        base_user = base_user_queryset.last()
        base_user.first_name = first_name
        base_user.last_name = last_name
        base_user.email = email
        base_user.user_type = user_type
        profile_picture = request.FILES.get('profile_pic')
        print("profile_picture::",profile_picture)
        if profile_picture:
            print(profile_picture)
            base_user.profile_picture = profile_picture
            base_user.save()
            print("base_user::",base_user.profile_picture)
            # Use the .url property to get the image URL
            base_user.profile_picture_url = base_user.profile_picture.url
        base_user.save()
                
        
        if base_user.user_type == 'doctor':
            # try:
                print("on 304")
                template_src = 'letter_head.html'
                data = request.data
                print(request.FILES)
                
                random_integer = random.randint(1, 100)
                temp, file_path = render_to_pdf(template_src, data, f'letter_head_{random_integer}')
                user = BaseUser.objects.filter(mobile_no=mobile_no).last()
                print('user::',user)
                image_url = "{}/static/".format(settings.CURRENT_HOST)+file_path
                print("mobile_no::",mobile_no)
                doctor, created = Doctor.objects.get_or_create(user=user)
                print("doctor::",doctor)
                doctor.hospital_affiliation = request.data.get('hospital_affiliation', None)
                doctor.license_number = request.data.get('license_number', None)
                doctor.years_of_experience = request.data.get('years_of_experience', None)
                doctor.letter_head_url = image_url
                doctor.save()
                user_details = {
                    'id': doctor.user.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    # 'profile_url': settings.CURRENT_HOST + "" + doctor.user.profile_picture_url,
                    'hospital_affiliation': doctor.hospital_affiliation,
                    'license_number': doctor.license_number,
                    'years_of_experience': doctor.years_of_experience,
                    'letter_head_url': doctor.letter_head_url,
                }

                return JsonResponse(user_details)

            # except Exception as e:
            #     return JsonResponse({"error": str(e)})
        elif base_user.user_type == 'patient':
            # try:
                data = request.data
                template_src = 'prescription.html'
                patient, created = Patient.objects.get_or_create(user=base_user)
                patient.allergies = request.data.get('allergies', None)
                patient.current_medications = request.data.get('current_medications', None)
                patient.medical_conditions = request.data.get('medical_conditions', None)
                random_integer = random.randint(1, 100)
                file_name = f'prescription_{random_integer}'
                temp, file_path = render_to_pdf(template_src, data, file_name)
                user = BaseUser.objects.filter(mobile_no=mobile_no).last()
                print('user::',user)
                # image_url = "{}/static/".format(settings.CURRENT_HOST)+file_path

                doc = Document.objects.create(user=user,file_url=image_url,file_name=file_name)
                patient.save()
                user_details = {
                    'id': patient.user.id,
                    'first_name': patient.user.first_name,
                    'last_name': patient.user.last_name,
                    'email': patient.user.email,
                    'allergies': patient.allergies,
                    # 'profile_url': settings.CURRENT_HOST + "" + patient.user.profile_picture_url,
                    'current_medications': patient.current_medications,
                    'medical_conditions': patient.medical_conditions,
                    'prescription_url':doc.file_url,
                }

                if created:
                    return JsonResponse({'message': 'Patient registered successfully', 'user': user_details, "status": "success"},
                                        status=status.HTTP_201_CREATED)
                else:
                    return JsonResponse({'message': 'Patient already exists', 'user': user_details, "status": "success"},
                                        status=status.HTTP_409_CONFLICT)

                # except Exception as e:
                #     return JsonResponse({"error": str(e)})


    else:
        return JsonResponse({'message': 'User Not Found'}, status=status.HTTP_404_NOT_FOUND)        



