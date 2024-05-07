import logging
log = logging.getLogger("app")

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
    access_control = serializers.CharField(read_only=False)

    class Meta:
        model = DataSet
        fields = ["data_set_id", "data_set_name", "users", "groups", "added", "updated", "access_control"]
        read_only_fields = ("data_set_id",)
        datatables_always_serialize = ("data_set_id",)

    def update(self, instance, validated_data):
        """ Update DataSet instance """

        if access_control := validated_data.pop("access_control", None):
            instance.access_control = access_control

        return instance