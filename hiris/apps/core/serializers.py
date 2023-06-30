from rest_framework import serializers

from hiris.apps.core.models import GenomeSpecies


class GenomeSpeciesSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for GenomeSpecies"""

    class Meta:
        model = GenomeSpecies
        fields = "__all__"
