"""
URL configuration for tracking project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('import-emails/', views.import_emails, name='import_emails'),
    path('send-emails/', views.send_emails, name='send_emails'),
    path('track-email/<str:tracking_id>/', views.track_email_open, name='track_email_open'),
    path('track-cta/<str:tracking_id>/', views.track_cta_click, name='track_cta_click'),
    path('delete-email/<str:tracking_id>/', views.delete_email, name='delete_email'),
    path('update-cold-leads/', views.update_cold_leads, name='update_cold_leads'),
]
