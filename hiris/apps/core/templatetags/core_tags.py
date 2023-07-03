from django import template

import logging
log = logging.getLogger('app')


register = template.Library()


@register.simple_tag(takes_context=True)
def pretty_name(context: dict) -> str:
    """ Return the pretty name of a user from the context """

    user = context.get('user')

    if user is None:
        return ""
    
    if name := user.get_full_name():
        return name

    return user.get_username()
