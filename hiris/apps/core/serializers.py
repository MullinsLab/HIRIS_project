from rest_framework import serializers

from hiris.apps.core.models import GenomeHost

class GenomeHostSerializer(serializers.HyperlinkedModelSerializer):
    ''' Serializer for GenomeHosts '''
    class Meta:
        model = GenomeHost
        fields = '__all__'