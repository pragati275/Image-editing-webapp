from django.shortcuts import render
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from PIL import Image
from uuid import uuid4
from botocore.exceptions import NoCredentialsError
import io
import base64
from datetime import datetime
import os
import cv2
import numpy as np
import mediapipe as mp  
import boto3

path = settings.MEDIA_ROOT
fs = FileSystemStorage()

# Create your views here.
def index(request):
    return render(request,'index.html')

def about(request):
    return render(request,'about.html')

def contact(request):
    return render(request,'contact.html')

@csrf_exempt
def captured(request):
    return render(request, 'capture.html')

@csrf_exempt
def image(request):
    return uploader(request, 'image_bg.html')

@csrf_exempt
def crop(request):
    return uploader(request, 'crop.html')
    
@csrf_exempt    
def change_color(request):
    return uploader(request, 'change_color.html')

@csrf_exempt
def sharpen_image(request):
    return uploader(request, 'sharpen.html')

def extension_check(photo):
    ext = os.path.splitext(photo.name)[1]
    if ext not in ['.png', '.jpg', '.jpeg', '.svg']:
        return True
@csrf_exempt
def uploader(request, html):
    context = {}
    if request.method == 'POST' and request.FILES.get('image'):
        uploaded_image = request.FILES['image']
        if extension_check(uploaded_image):
            return render(request, html, {'error': "Invalid File Type"})
        filename = fs.save(uploaded_image.name, uploaded_image)
        uploaded_file_url = fs.url(filename)
        context['bg_image'] = uploaded_file_url
        print("uploaded_file_url",uploaded_file_url)
        if html == "image_bg.html" and request.FILES.get('image0'):
            uploaded_image0 = request.FILES['image0']
            if extension_check(uploaded_image0):
                return render(request, html, {'error': "Invalid File Type"})
            filename0 = fs.save(uploaded_image0.name, uploaded_image0)
            uploaded_file_url0 = fs.url(filename0)
            context['input_image'] = uploaded_file_url0

        if html == 'sharpen.html':
            image1 = cv2.imread(path + uploaded_file_url.replace("/media", "/"))
            filtered = cv2.filter2D(image1, -1, np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]]))
            cv2.imwrite(path + "/sharp.png", filtered)
            context['output_image'] = fs.url('sharp.png')

    return render(request, html, context)

@csrf_exempt
def back(request):
    if request.method == 'POST':
        input_image_url = request.POST.get('input_image')
        bg_image_url = request.POST.get('bg_image')
        if not input_image_url or not bg_image_url:
            return JsonResponse({'error': 'Missing images'})

        input_image = cv2.imread(path + input_image_url.replace("media/", ""))
        bg_image = cv2.imread(path + bg_image_url.replace("media/", ""))
        output_image = perform_background_removal(input_image, bg_image)

        cv2.imwrite(path + "/input.png", input_image)
        cv2.imwrite(path + "/output.png", output_image)

        return render(request, 'image_bg.html', {
            'input_image': fs.url('input.png'),
            'bg_image': bg_image_url,
            'output_image': fs.url('output.png')
        })

@csrf_exempt
def cc(request):
    if request.method == 'POST':
        photo_url = request.POST.get('bg_image')
        if not photo_url:
            return JsonResponse({'error': 'Missing background image'})

        rgb = request.POST.get('rgb')
        if not rgb:
            return JsonResponse({'error': 'Missing RGB values'})

        rgb = list(map(int, rgb.split(",")))
        new_color_hex = request.POST.get('new-color')
        new_color = tuple(int(new_color_hex[i:i+2], 16) for i in (0, 2, 4))

        img = Image.open(path + photo_url.replace("/media", "/"))
        img = img.convert("RGB")
        pixel_array = np.array(img)
        rgb_img = pixel_array[..., :3]
        rgb_img[np.all(rgb_img == rgb, axis=-1)] = new_color
        pixel_array[..., :3] = rgb_img

        output = Image.fromarray(pixel_array)
        output.save(path + "/cco.png")
        return render(request, 'change_color.html', {
            'bg_image': photo_url,
            'output_image': fs.url('cco.png')
        })

@csrf_exempt
def crop1(request):
    if request.method == 'POST':
        print("POST data:", request.POST)
        photo_url = request.POST.get('bg_image')
        rect = request.POST.get('rectan')
        if not photo_url or not rect:
            return JsonResponse({'error': 'Missing parameters'})

        rect = list(map(int, rect.split(",")))
        if rect[2] < 0:
            rect[2] *= -1
            rect[0] -= rect[2]
        if rect[3] < 0:
            rect[3] *= -1
            rect[1] -= rect[3]
        print(path + photo_url.replace("/media", ""))
        image = Image.open(path + photo_url.replace("/media", ""))
        cropped_image = image.crop((rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3]))
        cropped_image.save(path + '/crop_output.png')
        return render(request, 'crop.html', {
            'bg_image': photo_url,
            'output_image': fs.url('crop_output.png')
        })

def perform_background_removal(image_np, bg):
    mp_selfie_segmentation = mp.solutions.selfie_segmentation
    selfie_segmentation = mp_selfie_segmentation.SelfieSegmentation(model_selection=1)

    RGB = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
    results = selfie_segmentation.process(RGB)
    mask = results.segmentation_mask
    condition = np.stack((mask,) * 3, axis=-1) > 0.6

    custom_bg_image = cv2.resize(bg, (image_np.shape[1], image_np.shape[0]))
    processed_image_np = np.where(condition, image_np, custom_bg_image)
    return processed_image_np