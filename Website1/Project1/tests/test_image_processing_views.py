# your_app/tests/test_image_processing_views.py

import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
import os
from PIL import Image
import io
import tempfile

@pytest.fixture
def sample_image():
    # Create a simple 100x100 red image for testing
    img = Image.new('RGB', (100, 100), color = 'red')
    img_io = io.BytesIO()
    img.save(img_io, 'JPEG')
    img_io.seek(0)
    return SimpleUploadedFile("test.jpg", img_io.read(), content_type="image/jpeg")

@pytest.fixture
def sample_bg_image():
    # Create a simple 100x100 blue image for testing
    img = Image.new('RGB', (100, 100), color = 'blue')
    img_io = io.BytesIO()
    img.save(img_io, 'JPEG')
    img_io.seek(0)
    return SimpleUploadedFile("bg_test.jpg", img_io.read(), content_type="image/jpeg")

@pytest.mark.django_db
class TestUploaderViews:
    def test_captured_view_get(self, client):
        response = client.get(reverse('captured'))
        assert response.status_code == 200
        assert 'capture.html' in [t.name for t in response.templates]

    def test_image_view_get(self, client):
        response = client.get(reverse('imagebg'))
        assert response.status_code == 200
        assert 'image_bg.html' in [t.name for t in response.templates]

    def test_crop_view_get(self, client):
        response = client.get(reverse('crop'))
        assert response.status_code == 200
        assert 'crop.html' in [t.name for t in response.templates]

    def test_change_color_view_get(self, client):
        response = client.get(reverse('change_color'))
        assert response.status_code == 200
        assert 'change_color.html' in [t.name for t in response.templates]

    def test_sharpen_image_view_get(self, client):
        response = client.get(reverse('sharpen'))
        assert response.status_code == 200
        assert 'sharpen.html' in [t.name for t in response.templates]


    def test_image_upload_success(self, client):
        image_file = SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        image_file0 = SimpleUploadedFile("test0.jpg", b"file_content", content_type="image/jpeg")

        response = client.post(
            '/imagebg/',
            {'image': image_file, 'image0': image_file0},
            format='multipart',
        )
        assert response.status_code == 200
        assert 'bg_image' in response.context


    def test_image_upload_invalid_extension(self, client):
        invalid_file = SimpleUploadedFile("test.txt", b"file_content", content_type="text/plain")
        response = client.post(reverse('imagebg'), {'image': invalid_file})
        assert response.status_code == 200
        assert 'error' in response.context
        assert response.context['error'] == "Invalid File Type"

    def test_image_bg_upload_success(self, client, sample_image, sample_bg_image):
        # First upload background image
        response = client.post(reverse('imagebg'), {'image': sample_image, 'image0': sample_bg_image})
        assert response.status_code == 200
        assert 'input_image' in response.context
        assert 'bg_image' in response.context
        assert response.context['input_image'].startswith(settings.MEDIA_URL)
        assert response.context['bg_image'].startswith(settings.MEDIA_URL)

    def test_crop_upload_success(self, client, sample_image):
        response = client.post(reverse('crop'), {'image': sample_image})
        assert response.status_code == 200
        assert 'bg_image' in response.context
        assert response.context['bg_image'].startswith(settings.MEDIA_URL)

    def test_sharpen_image_upload_success(self, client, sample_image):
        response = client.post(reverse('sharpen'), {'image': sample_image})
        assert response.status_code == 200
        assert 'output_image' in response.context
        assert response.context['output_image'].startswith(settings.MEDIA_URL)

    def test_process_image_invalid_request(self, client):
        response = client.post(reverse('process_image'), {})
        assert response.status_code == 200
        response_data = response.json()
        assert 'error' in response_data
        assert response_data['error'] == "Error"

    def test_back_view(self, client, sample_image, sample_bg_image):
            # Upload images first
        client.post(reverse('imagebg'), {'image': sample_image, 'image0': sample_bg_image})
        # Call back view
        response = client.get(reverse('back'))
        assert response.status_code == 200
        assert 'input_image' in response.context
        assert 'bg_image' in response.context
        assert 'output_image' in response.context
        assert response.context['input_image'].startswith(settings.MEDIA_URL)
        assert response.context['bg_image'].startswith(settings.MEDIA_URL)
        assert response.context['output_image'].startswith(settings.MEDIA_URL)

    def test_crop1_view_success(self, client, sample_image):
        # Upload image first
        client.post(reverse('crop'), {'image': sample_image})
        # Perform cropping
        response = client.post(reverse('crop1'), {
            'rectan': '10,10,50,50'
        })
        assert response.status_code == 200
        assert 'bg_image' in response.context
        assert 'output_image' in response.context
        assert response.context['bg_image'].startswith(settings.MEDIA_URL)
        assert response.context['output_image'].startswith(settings.MEDIA_URL)

    def test_crop1_view_invalid_rect(self, client):
        # Create a temporary image file
        with tempfile.NamedTemporaryFile(suffix=".jpg") as tmp_img:
            image = Image.new('RGB', (100, 100), color=(255, 255, 255))
            image.save(tmp_img, format='JPEG')
            tmp_img.seek(0)  # Rewind file pointer for reading

            response = client.post(
                '/crop1/',
                {'image': tmp_img, 'rectan': '10,10,-20,-20'},  # Invalid rectangle
                format='multipart',
            )
        assert response.status_code == 200
        assert 'output_image' in response.context

## Adding A COMMENT for testing
