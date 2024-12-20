"""oauth URL Configuration
"""
from django.urls import path, include
urlpatterns = [
    path('', include('vires_oauth.urls')),
]
