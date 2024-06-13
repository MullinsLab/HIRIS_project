import logging
log = logging.getLogger("app")

from django.contrib.auth.models import User, Group
from django.db.models import Count
from django.http import JsonResponse
from django.views.generic.base import View

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from rest_framework_datatables.django_filters.backends import DatatablesFilterBackend

from hiris.apps.core import models, serializers, filters

class GenomeSpeciesViewSet(viewsets.ModelViewSet):
    """ ViewSet for viewing and editing GenomeSpecies objects """

    queryset = models.GenomeSpecies.objects.all()
    serializer_class = serializers.GenomeSpeciesSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """ ViewSet for viewing and editing Group objects """

    queryset = Group.objects.all()
    serializer_class = serializers.GroupSerializer


class UserViewSet(viewsets.ModelViewSet):
    """ ViewSet for viewing and editing User objects """

    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer

    filter_backends = (DatatablesFilterBackend, )
    filterset_class = filters.UserGlobalFilter

    @action(detail=False)
    def groups(self, request, *args, **kwargs):
        """ Returns list of groups with user count """

        filters: dict = {}

        filter_dict: dict = {f"{filters[key]}__in": value.split("|") for key, value in request.GET.items() if key in filters}
        queryset = self.filter_queryset(self.get_queryset()).filter(**filter_dict)
        result_list = queryset.values('groups__name').annotate(count=Count('pk')).order_by()

        return Response(result_list)
    

class DataSetViewSet(viewsets.ModelViewSet):
    """ ViewSet for viewing and editing DataSet objects """

    queryset = models.DataSet.objects.all()
    serializer_class = serializers.DataSetSerializer
    filterset_fields = ["data_set_id"]


class LimitDataSets(View):
    """ Manage what data_sets are included in exports and graphs
        This Should use the DRF framework, but I'm out of time to work on this project, so it's a simple view """

    def get(self, request, *args, **kwargs) -> JsonResponse:
        """ Returns the limited data sets """

        json: dict = {}
        session_data_sets: list[int] = request.session.get("data_sets", [])

        for data_set in models.DataSet.objects.all():
            json[data_set.pk] = {"name": data_set.data_set_name, "selected": data_set.pk in session_data_sets}

        return JsonResponse(json)
    
    def post(self, request, *args, **kwargs) -> JsonResponse:
        """ Updates the session data sets """

        request.session["data_sets"] = request.POST.getlist("data_sets[]")

        return self.get(request, *args, **kwargs)