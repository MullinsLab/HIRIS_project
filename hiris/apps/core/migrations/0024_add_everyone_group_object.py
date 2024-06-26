from django.db import migrations
from django.db.models import Q
# from django.contrib.auth.models import Group, User


def add_everyone_group(apps, schema_editor):
    """ Create a group for everyone """

    User = apps.get_model("auth", "User")
    Group = apps.get_model("auth", "Group")

    everyone = Group.objects.create(name="Everyone")

    try:
        anonymous = User.objects.get(username="AnonymousUser")
    except User.DoesNotExist:
        User.objects.create(username="AnonymousUser")
    
    users = User.objects.filter(~Q(username="AnonymousUser"))

    everyone.user_set.add(*users)


def remove_everyone_group(apps, schema_editor):
    """ Remove the group for everyone """

    Group = apps.get_model("auth", "Group")
    Group.objects.get(name="Everyone").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0023_alter_dataset_options"),
    ]

    operations = [migrations.RunPython(add_everyone_group, remove_everyone_group)]
