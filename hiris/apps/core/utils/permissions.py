import logging
log = logging.getLogger('app')

from functools import cache

from django.contrib.auth.models import User


@cache
def get_anonymous_user() -> User:
    """ Return the anonymous user """

    return User.objects.get(username="AnonymousUser")


def object_is_public(object) -> bool:
    """ Check if an object is public """

    return get_anonymous_user().has_perm('core.view_dataset', object) 
