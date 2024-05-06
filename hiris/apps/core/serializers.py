from rest_framework import serializers


from django.contrib.auth.models import User, Group

from hiris.apps.core.models import GenomeSpecies, DataSet


class GenomeSpeciesSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializer for GenomeSpecies """

    class Meta:
        model = GenomeSpecies
        fields = '__all__'


class GroupSerializer(serializers.ModelSerializer):
    """ Serializer for Group """

    class Meta:
        model = Group
        fields = ["id", "name"]
        datatables_always_serialize=("id",)


class UserSerializer(serializers.ModelSerializer):
    """ Serializer for User """

    groups = GroupSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email", "username", "groups"]
        datatables_always_serialize = ("id", )


class DataSetSerializer(serializers.ModelSerializer):
    """ Serializer for DataSet """

    users = UserSerializer(many=True, read_only=False)
    groups = GroupSerializer(many=True, read_only=False)

    class Meta:
        model = DataSet
        fields = '__all__'
        datatables_always_serialize = ("data_set_id",)