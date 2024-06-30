from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_file, name='upload_file'),
    path('download/<str:filename>/', views.download_file, name='download_file'),
]
