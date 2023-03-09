from django.conf import settings
from django import template

import logging
log = logging.getLogger(settings.ML_IMPORT_WIZARD['Logger'])


register = template.Library()

@register.filter()
def get_item(dictionary: dict, key: str) -> any:
    """ Custom filter to return the value of a key from a dict """
    log.debug(f"Getting value from dict: {dict} with key: {key}, resulting in {dictionary.get(key)}")
    return dictionary.get(key)

@register.simple_tag
def log_debug(value: any) -> None:
    """ Custom tag to log whatever is passed to it """
    log.debug(f"Logging from template: {value}")