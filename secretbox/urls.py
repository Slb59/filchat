#filchat.urls.py
from django.urls import path

from . import views

app_name = 'secretbox'

urlpatterns = [
    path('', views.home, name='home'),
]