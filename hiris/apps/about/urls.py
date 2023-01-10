

from django.contrib.auth.decorators import login_required
from django.urls import path, include

from hiris.apps.about import views

# determine appname
app_name='hiris.apps.about'

urlpatterns = [
     path('', views.About.as_view(), name='about'),
]
