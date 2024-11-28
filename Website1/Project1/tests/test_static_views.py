# your_app/tests/test_static_views.py

import pytest
from django.urls import reverse

@pytest.mark.django_db
class TestStaticViews:
    def test_index_view(self, client):
        response = client.get(reverse('index'))
        assert response.status_code == 200
        assert 'index.html' in [t.name for t in response.templates]

    def test_about_view(self, client):
        response = client.get(reverse('about'))
        assert response.status_code == 200
        assert 'about.html' in [t.name for t in response.templates]

    def test_contact_view(self, client):
        response = client.get(reverse('contact'))
        assert response.status_code == 200
        assert 'contact.html' in [t.name for t in response.templates]

    def test_pricing_view(self, client):
        response = client.get(reverse('pricing'))
        assert response.status_code == 200
        assert 'pricing.html' in [t.name for t in response.templates]

    def test_privacy_view(self, client):
        response = client.get(reverse('privacy'))
        assert response.status_code == 200
        assert 'privacy.html' in [t.name for t in response.templates]
