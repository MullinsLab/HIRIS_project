from django.conf import settings
from django import template

import logging
log = logging.getLogger(settings.ML_IMPORT_WIZARD['Logger'])

from ml_import_wizard.utils.simple import json_dump, fancy_name

register = template.Library()


@register.filter()
def get_item(dictionary: dict, key: str) -> any:
    """ Custom filter to return the value of a key from a dict """

    # log.debug(f"Getting value from dict: {dict} with key: {key}, resulting in {dictionary.get(key)}")
    return dictionary.get(key)


@register.simple_tag
def log_debug(value: any) -> None:
    """ Custom tag to log whatever is passed to it """

    log.debug(f"Logging from template: {value}")


@register.filter()
def verbose_name(field: object) -> str:
    """" Custom tag to return the verbose_name given a field object """

    if field.field.verbose_name.islower():
        return fancy_name(field.field.verbose_name)
    return field.field.verbose_name