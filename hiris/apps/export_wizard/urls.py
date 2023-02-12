from django.contrib.auth.decorators import login_required
from django.urls import path, include

from hiris.apps.export_wizard import views

# determine appname
app_name='hiris.apps.core'

urlpatterns = [
     path('', views.StartExport.as_view(), name='about'),
]