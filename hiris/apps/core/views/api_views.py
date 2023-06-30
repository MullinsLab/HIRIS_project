from rest_framework import viewsets
from rest_framework import generics

from hiris.apps.core.models import GenomeSpecies
from hiris.apps.core.serializers import GenomeSpeciesSerializer


class GenomeSpecies(viewsets.ModelViewSet):
    queryset = GenomeSpecies.objects.all()
    serializer_class = GenomeSpeciesSerializer
