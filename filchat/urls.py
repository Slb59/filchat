#filchat.urls.py
from django.urls import path

from . import views

urlpatterns = [
    path('upload/', views.upload_file, name='upload_file'),
    path('process/<int:file_id>/', views.process_file, name='process_file'),
    path('download/<int:file_id>/', views.download_file, name='download_file'),
]