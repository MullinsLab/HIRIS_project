""" Holds custom managers for the viroserve app """

import logging
log = logging.getLogger("app")

import re

from django.db import models
from django.db.models import Model, Q
from django.db.models.fields.related import RelatedField

from hiris.utils_early import get_request_object

class DataSetLimitingManager(models.Manager):
    """ Manager that limits the queryset to cohorts that the scientist has access to """

    def get_queryset(self):
        """ Return a queryset limited to the current scientsist """

        from hiris.utils import current_user 

        if request := get_request_object():
            user = current_user()
            
            if not user.is_staff:
                user_q: Q = Q(**{f"{models_graph.path_to[self.model.__name__]}users": user})
                group_q: Q = Q(**{f"{models_graph.path_to[self.model.__name__]}groups__in": user.groups.all()})

                return super().get_queryset().distinct().filter(user_q | group_q)
        
        return super().get_queryset()
    

class ModelsGraph(object):
    """ Makes a graph of models so we can find a path between two models """

    def __init__(self, *, app: str = None, start_with: Model = None, initial_path_string: str = None, exclude_models: list[Model] = None, exclude_from_path: list[Model] = None) -> None:  
        """ Set up the graph """

        self.path_to: dict[str: str] = {}

        model_stack: list[Model] = []

        def process_model(model: Model) -> None:
            """ Recursively find paths to all child models """

            related_models: list[tuple[str, str]] = [field.related_model for field in model._meta.get_fields() if isinstance(field, RelatedField)]
            related_models += [related_object.related_model for related_object in model._meta.related_objects]

            for related_model in related_models:
                if related_model.__name__ not in self.path_to and related_model not in exclude_models:
                    self.path_to[related_model.__name__] = f"{return_path(related_model, model)}__{self.path_to[model.__name__]}"
                    if related_model not in exclude_from_path:
                        model_stack.append(related_model)

        # Add start_with to kick things off
        self.path_to[start_with.__name__] = initial_path_string
        model_stack.append(start_with)

        while model_stack:
            process_model(model_stack.pop(0))

# Make a global models graph object
models_graph: ModelsGraph = None


def _model_to_manager(name):
    """ Converts a model name to a manager name """

    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def return_path(from_model: Model, to_model: Model) -> str:
    """ Returns the path name between two models """

    relations: list[tuple[str, str]] = [(field.name, field.related_model) for field in from_model._meta.get_fields() if isinstance(field, RelatedField) and field.related_model == to_model]
    relations += [(related_object.related_name or _model_to_manager(related_object.name), related_object.related_model) for related_object in from_model._meta.related_objects if related_object.related_model == to_model]

    if len(relations) == 1:
        return relations[0][0]
    
    if isinstance(to_model.name, str):
        if to_model.name.lower() in [relation[0] for relation in relations]:
            return to_model.__name__.lower()
    
    if manager_name := _model_to_manager(to_model.__name__) in [relation[0] for relation in relations]:
        return manager_name
    
    return relations[0][0]