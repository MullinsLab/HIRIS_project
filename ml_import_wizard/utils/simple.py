from django.contrib.auth.models import User

from typing import Dict, Any
import hashlib
import json


def dict_hash(dictionary: Dict[str, Any]) -> str:
    """MD5 hash of a dictionary."""
    dhash = hashlib.md5()
    # We need to sort arguments so {'a': 1, 'b': 2} is
    # the same as {'b': 2, 'a': 1}
    encoded = json.dumps(dictionary, sort_keys=True).encode()
    dhash.update(encoded)
    return dhash.hexdigest()


def sound_user_name(user: User) -> str:
    ''' Get a sound name for the user.  First match of "first_name last_name", "first_name", "last_name", "username"'''
    if user.first_name and user.last_name:
       return f'{user.first_name} {user.last_name}'
    
    return user.first_name or user.last_name or user.username


def mached_name_choices(choices: list) -> list:
    """ Functin to return a list of tuples that contains the origional list doubled
    ['thing1', 'thing2'] becomes [('thing1', 'thing1'), ('thing2', thing2')] """
    
    tuple_choices: list = []
    for choice in choices:
        tuple_choices.append((choice, choice))
        
    return tuple_choices


def stringilize(value: any = None) -> str:
    """ Make sure a value is a string.  Doesn't include enclosures ([{}]) """

    if type(value) in [tuple, list, set]:
        return', '.join([str(item) for item in value])
    else:
        return str(value)