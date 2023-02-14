from django.urls import path, include

from rest_framework import routers

from hiris.apps.core import views

router = routers.DefaultRouter()
router.register(r'genome_hosts', views.GenomeHosts)

# determine appname
app_name='hiris.apps.core'

urlpatterns = [
     path('', include(router.urls)),
]