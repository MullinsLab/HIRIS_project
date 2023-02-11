from rest_framework import viewsets
from rest_framework import generics

from hiris.apps.core.models import GenomeHost
from hiris.apps.core.serializers import GenomeHostSerializer

class GenomeHosts(viewsets.ModelViewSet):
    queryset = GenomeHost.objects.all()
    serializer_class = GenomeHostSerializer