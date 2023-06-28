import logging
log = logging.getLogger('app')

import hashlib, json
from typing import Dict, Any

def underscore_keys(dict: dict) -> dict:
    """ Returns the dictionary with the keys slugified """

    return {key.replace(" ","_"): value for key, value in dict.items()}


def group_dict_list(*, dict_list: list=None, key: str=None, no_key_name: str="**no_keys**") -> dict:
    """ Take a list of dicts that have a common key and turn into a dict of those keys each containing a list of the dicts """

    out_dictionary: dict[list] = {}

    for dictionary in dict_list:
        if key in dictionary:
            if dictionary[key] not in out_dictionary:
                out_dictionary[dictionary[key]] = []

            out_dictionary[dictionary[key]].append(dictionary)
        else:
            if no_key_name not in out_dictionary:
                out_dictionary[no_key_name] = []
            
            out_dictionary[no_key_name].append(dictionary)
            
    return out_dictionary


def first_author(authors: str=None) -> str:
    """ Returns the first author from an authors string """

    if not authors:
        return None
    
    first_bit = authors.split("and")[0]

    return first_bit


def dict_hash(dictionary: Dict[str, Any]) -> str:
    """ MD5 hash of a dictionary """
    dhash = hashlib.md5()
    # We need to sort arguments so {'a': 1, 'b': 2} is
    # the same as {'b': 2, 'a': 1}
    encoded = json.dumps(dictionary, sort_keys=True).encode()
    dhash.update(encoded)
    return dhash.hexdigest()