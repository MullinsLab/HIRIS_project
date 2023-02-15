from django.contrib.auth.decorators import login_required
from django.urls import path, include

from hiris.apps.core import views

# determine appname
app_name='hiris.apps.core'

urlpatterns = [
     path('', views.Home.as_view(), name='about'),
]
