from rest_framework import viewsets
from rest_framework import generics

from django.contrib.auth.models import User, Group

from hiris.apps.core.models import GenomeSpecies
from hiris.apps.core.serializers import GenomeSpeciesSerializer, UserSerializer


class GenomeSpeciesViewSet(viewsets.ModelViewSet):
    """ ViewSet for viewing and editing GenomeSpecies objects """

    queryset = GenomeSpecies.objects.all()
    serializer_class = GenomeSpeciesSerializer


class UserViewSet(viewsets.ModelViewSet):
    """ ViewSet for viewing and editing User objects """

    queryset = User.objects.all()
    serializer_class = UserSerializer