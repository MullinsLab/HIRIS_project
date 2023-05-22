from django.contrib.auth.decorators import login_required
from django.urls import path, include

import logging
log = logging.getLogger('app')

from hiris.apps.core import views

# determine appname
app_name='tools'

urlpatterns = [
     path('', views.Home.as_view(), name='about'),
     path('datasources', views.DataSources.as_view(), name='data_sources'),
]
