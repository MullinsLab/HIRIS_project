import logging
log = logging.getLogger("app")

from django.contrib.auth.models import User, Group
from django.db.models import Count

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

    # filter_backends = (DatatablesFilterBackend, )
    # filterset_fields = '__all__'
    # filterset_class = filters.DataSetFilter