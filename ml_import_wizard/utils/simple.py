# from django.contrib.auth.models import User # Caused circular import
from django.conf import settings

import logging
log = logging.getLogger(settings.ML_IMPORT_WIZARD['Logger'])

from typing import Dict, Any
import hashlib
import json
import jsonpickle
import re


def dict_hash(dictionary: Dict[str, Any]) -> str:
    """ MD5 hash of a dictionary """
    dhash = hashlib.md5()
    # We need to sort arguments so {'a': 1, 'b': 2} is
    # the same as {'b': 2, 'a': 1}
    encoded = json.dumps(dictionary, sort_keys=True).encode()
    dhash.update(encoded)
    return dhash.hexdigest()


def sound_user_name(user: object) -> str: # object should be user, but importing user caused a circular import
    ''' Get a sound name for the user.  First match of "first_name last_name", "first_name", "last_name", "username"'''
    if user.first_name and user.last_name:
       return f'{user.first_name} {user.last_name}'
    
    return user.first_name or user.last_name or user.username


def mached_name_choices(choices: list) -> list[tuple]:
    """ Functin to return a list of tuples that contains the origional list doubled
    ['thing1', 'thing2'] becomes [('thing1', 'thing1'), ('thing2', thing2')] """
    
    tuple_choices: list[tuple] = []
    for choice in choices:
        tuple_choices.append((choice, choice))
        
    return tuple_choices


def stringalize(value: any = None) -> str:
    """ Forces a value into a string.  Doesn't include enclosures ([{}]) """

    if type(value) in [tuple, list]:
        return', '.join([str(item) for item in value])
    if type(value) == set:
        return', '.join([str(item) for item in sorted(value, key=str)])
    else:
        return str(value)
    

def split_by_caps(value: str = '') -> list[str]:
    """ Returns a list of strings split by capitol letters """
    
    return [s for s in re.split("([A-Z][^A-Z]*)", value) if s]


def fancy_name(value: str = '') -> str:
    """ returns the 'Fancy Name' of a string """

    value = " ".join(value.split("_"))
    value = " ".join(split_by_caps(value))
    value = value.title()

    # Capitalize ID so it doesn't show as Id
    value = value.replace(" Id ", " ID ")
    value = re.sub("^Id ", "ID ", value)
    value = re.sub(" Id$", " ID", value)
    if value == "Id": value = "ID"

    return value


def json_dump(object: object) -> str:
    """ Returns a json dump of the object, mostly for logging """

    return json.dumps(jsonpickle.encode(object, unpicklable=False))


def resolve_true(value: any) -> bool|None:
    """ Resolves ambiguous values to true or false """

    if type(value) is str:
        if value.lower() in ("no", "false", "0"):
            return False

    if value is None:
        return None
    
    return bool(value)