
def underscore_keys(dict: dict) -> dict:
    """ Returns the dictionary with the keys slugified """

    return {key.replace(" ","_"): value for key, value in dict.items()}