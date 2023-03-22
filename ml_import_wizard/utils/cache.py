from django.conf import settings

import logging
log = logging.getLogger(settings.ML_IMPORT_WIZARD['Logger'])

from collections import OrderedDict


class LRUCacheThing():
    """" Cache things with Least Recently Used.  Has stupid name to avoid colisions """

    def __init__(self, *, items: int=100):
        """ Initialize with 100 items by default """

        self.things = OrderedDict()
        self.items = items
    
    def store(self, *, key: any, value: any) -> any:
        """ Store a key/value in the cache """

        self.things[key] = value
        self.things.move_to_end(key)

        if len(self.things) > self.items:
            self.things.popitem(last=False)

    def find(self, *, key: any, report: bool=False, output: str="print") -> any:
        """ Return the object found using the key, or none """

        if key in self.things:
            self.things.move_to_end(key)
            if report: 
                if output == "print":
                    print(f"Found key: {key}")
                else:
                    log.debug(f"Found key: {key}")

            return self.things[key]
        
        if report: 
            if output == "print":
                print(f"Didn't find key: {key}")
            else:
                log.debug(f"Didn't find key: {key}")
        return None