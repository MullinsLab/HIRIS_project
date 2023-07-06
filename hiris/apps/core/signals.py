import logging
log = logging.getLogger('app')

from django.dispatch import receiver
from django.db.models.signals import post_save

from django.contrib.auth.models import User, Group


@receiver(post_save, sender=User, dispatch_uid="register_user_everyone_callback")
def user_everyone_callback(sender, instance, created, **kwargs):
    """ Signal callback to add all new users to the Everyone group """

    if created:
        everyone: Group = Group.objects.get(name="Everyone")
        everyone.user_set.add(instance)