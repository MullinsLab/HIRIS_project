from django.contrib.auth.decorators import login_required
from django.urls import path, include

import logging
log = logging.getLogger('app')

from hiris.apps.core import views

# determine appname
app_name='admin'

urlpatterns = [
    path("users/", views.UsersList.as_view(), name="user_list"),
    path("users/<int:pk>/", views.UserUpdate.as_view(), name="user_update"),
    path("users/<int:pk>/password/", views.UserPassword.as_view(), name="user_password"),
    path("users/create/", views.UserCreate.as_view(), name="user_create"),
]
