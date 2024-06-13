from django.urls import path, include

from rest_framework import routers

from hiris.apps.core import views

router = routers.DefaultRouter()
router.register(r"genome_hosts", views.GenomeSpeciesViewSet, basename="genome_host")
router.register(r"groups", views.GroupViewSet, basename="group")
router.register(r"users", views.UserViewSet, basename="user")
router.register(r"data_sets", views.DataSetViewSet, basename="data_set")

# determine appname
app_name="api"

urlpatterns = [
    path('', include(router.urls)),
    path("limit_data_sets", views.LimitDataSets.as_view(), name="limit_data_sets"),
]