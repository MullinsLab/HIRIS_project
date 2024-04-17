from rest_framework import serializers

from hiris.apps.core.models import GenomeSpecies
from django.contrib.auth.models import User, Group


class GenomeSpeciesSerializer(serializers.HyperlinkedModelSerializer):
    ''' Serializer for GenomeSpecies '''

    class Meta:
        model = GenomeSpecies
        fields = '__all__'


class UserSerializer(serializers.HyperlinkedModelSerializer):
    ''' Serializer for User '''

    group = serializers.StringRelatedField()

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'group']