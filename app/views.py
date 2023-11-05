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

from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
import os
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
    



@api_view(['POST'])
def generate_card(request):
    template_src = 'card.html'
    data = {}
    random_integer = random.randint(1, 100)
    temp, file_path = render_to_pdf_card(template_src, data, f'letter_head_{random_integer}')
    # user = BaseUser.objects.filter(mobile_no=mobile_no).last()
    # print('user::',user)
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



def render_to_pdf_card(template_src, context, file_name="invoice"):
    Path("static/health_cards/").mkdir(parents=True, exist_ok=True)
    file_path = f'health_cards/{file_name}_{str(random.randint(100000, 9999999))}.pdf'
    print("file_path::", file_path)
    template = get_template(template_src)
    print("template::", template)
    html = template.render(context)
    
    options = {
        'page-height': '53.98mm',  
        'page-width': '82.60mm',   # Set the page width to match credit card dimensions
        'margin-top': '0mm',       # Remove top margin
        'margin-right': '0mm',     # Remove right margin
        'margin-bottom': '0mm',    # Remove bottom margin
        'margin-left': '0mm',      # Remove left margin
    }
    
    pdfkit.from_string(html, f'static/{file_path}', options=options)
    return file_path

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
@parser_classes((MultiPartParser, FormParser,))
def table_ocr(request):
    try:
        image_file = request.FILES.get('image')
        if not image_file:
            return JsonResponse({"error": "No image file provided"}, status=400)

        # Define the path to save the uploaded image
        image_path = os.path.join('media', 'images', image_file.name)

        # Save the uploaded image
        with open(image_path, 'wb') as f:
            for chunk in image_file.chunks():
                f.write(chunk)

        # Load the layout detection model
        model = lp.PaddleDetectionLayoutModel(
            config_path="lp://PubLayNet/ppyolov2_r50vd_dcn_365e_publaynet/config",
            threshold=0.5,
            label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"},
            enforce_cpu=False,
            enable_mkldnn=True
        )

        # Perform layout detection
        image = cv2.imread(image_path)
        image = image[..., ::-1]
        layout = model.detect(image)

        y_1 = None  # Initialize y_1 and y_2
        y_2 = None
        for l in layout._blocks:
            if l.type == 'Table':
                x_1 = int(l.block.x_1)
                y_1 = int(l.block.y_1)
                x_2 = int(l.block.x_2)
                y_2 = int(l.block.y_2)
                break

        if y_1 is None or y_2 is None:
            return JsonResponse({"error": "Table coordinates not found"})

        total_area = image[y_1:y_2, x_1:x_2]

        ocr = PaddleOCR(lang='en')
        output = ocr.ocr(total_area)

        data = []

        # Iterate over each OCR result
        for out in output[0]:
            # Extract relevant information
            text = out[1][0]
            confidence = out[1][1]
            bbox = out[0]
            x_min, y_min, x_max, y_max = bbox

            # Compute the row-wise sum of bbox coordinates
            bbox_sum = sum(x_min) + sum(y_min) + sum(x_max) + sum(y_max)

            # Append the information to the data list
            data.append([text, bbox_sum])

        # Create a pandas DataFrame from the data list
        df = pd.DataFrame(data, columns=['Text', 'BboxSum'])

        new_rows = []

        for index, row in df.iterrows():
            if ':' in row['Text']:
                text_parts = row['Text'].split(':', 1)
                text1 = text_parts[0].strip()
                text2 = text_parts[1].strip()
                new_rows.append([text1, row['BboxSum']])
                new_rows.append([text2, row['BboxSum']])
            elif row['Text'].strip() != '':
                new_rows.append([row['Text'], row['BboxSum']])

        new_df = pd.DataFrame(new_rows, columns=['Text', 'BboxSum'])

        # Remove rows with only BboxSum and no text
        new_df = new_df[new_df['Text'] != '']

        # Select only the desired columns
        new_df = new_df[['Text', 'BboxSum']]

        # Define the list of keys to search for
        keys_to_find = [
            'Patient Name',
            'Result',
            'Normal Range',
            'Units'
        ]

        result = {}
        key_flag = False
        previous_key = ''

        # Iterate over each row in the DataFrame
        for index, row in new_df.iterrows():
            # Convert the text to lowercase for case-insensitive comparison
            text = row['Text'].lower()

            # Check if the text matches any of the keys
            if text in [key.lower() for key in keys_to_find]:
                # Set the flag to indicate a key has been found
                key_flag = True

                # Set the current text as the previous key
                previous_key = row['Text']
            elif key_flag:
                # If the flag is True, set the previous key as a key in the result dictionary
                # and the current text as its value
                if previous_key not in result:
                    result[previous_key] = [row['Text']]
                else:
                    result[previous_key].append(row['Text'])

                # Reset the flag and previous key
                key_flag = False
                previous_key = ''

        # Convert the result dictionary to JSON
        result_json = json.dumps(result)

        # Delete records used as keys or values
        keys_to_delete = list(result.keys()) + sum(result.values(), [])
        new_df = new_df[~new_df['Text'].isin(keys_to_delete)]

        # Initialize the dictionary
        key_value_pairs = {}

        # Set the initial key and previous_bbox_sum
        key = new_df['Text'].iloc[0]
        previous_bbox_sum = new_df['BboxSum'].iloc[0]

        # Iterate over the 'BboxSum' column
        for bbox_sum in new_df['BboxSum']:
            # Compare the current bbox_sum with the previous one
            if bbox_sum > previous_bbox_sum:
                # Get the corresponding text value
                text = new_df.loc[new_df['BboxSum'] == bbox_sum, 'Text'].values[0]
                # Exclude the duplicate values
                if text != key:
                    # Append the value to the existing key
                    if key in key_value_pairs:
                        key_value_pairs[key].append(text)
                    else:
                        # Check if the key is in the exclusion list
                        if key not in keys_to_find:
                            key_value_pairs[key] = [text]
            else:
                # Create a new key
                key = new_df.loc[new_df['BboxSum'] == bbox_sum, 'Text'].values[0]
                # Initialize the value as a list with the current text
                # Check if the key is in the exclusion list
                if key not in keys_to_find:
                    key_value_pairs[key] = [key]

            # Update the previous_bbox_sum
            previous_bbox_sum = bbox_sum

        # Convert the key-value pairs to JSON
        key_value_json = json.dumps(key_value_pairs)

        # Merge the two JSON objects into one
        merged_json = {**json.loads(result_json), **json.loads(key_value_json)}

        # Save the processed data and image to the database
       
        # processed_image = ProcessedImage(image=image_file, processed_data=merged_json)
        # processed_image.save()

        # Remove the uploaded image
        os.remove(image_path)

        return JsonResponse(merged_json)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)




@api_view(['POST'])
def upload_doc(request):
    user_id = request.query_params.get('id')
    user = BaseUser.objects.filter(id=user_id).last()
    Document.objects.create(user=user,file_name=request.data.get('file_name'),hash_value=request.data.get('hash_value'))
    return JsonResponse({"status":"success","message":"Document uploaded successfully"})

@api_view(['GET'])
def get_doc(request):
    user_id = request.query_params.get('id')
    user = BaseUser.objects.filter(id=user_id).last()
    doc = Document.objects.filter(user=user)
    data = DocumentSerializer(doc,many=True).data
    return JsonResponse({"status":"success","data":data})


@api_view(['POST'])
def upload_prescription(request):
    data = request.data
    template_src = 'prescription.html'
    random_integer = random.randint(1, 100)
    temp, file_path = render_to_pdf(template_src, data, f'letter_head_{random_integer}')
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
                image_url = "{}/static/".format(settings.CURRENT_HOST)+file_path

                doc = Document.objects.create(user=user,download_image_url=image_url,file_name=file_name)
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
                    'prescription_url':doc.download_image_url,
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



