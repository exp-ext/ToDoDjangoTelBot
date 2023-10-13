from typing import OrderedDict

from django.core.serializers import deserialize, serialize
from django.db import models


class ModelDataSerializer():

    @staticmethod
    def serialize(model: models.Model, many: bool = False) -> OrderedDict:
        """Сериализация модели.

        ### Args:
        - model (`models.Model`): объект класса Model
        - many (`bool`): Models queryset если True

        ### Returns:
        - `OrderedDict`: сериализованные данные
        """
        if many:
            return serialize('python', model)
        return serialize('python', [model])

    @staticmethod
    def deserialize(serialized_data: OrderedDict, many: bool = False) -> models.Model:
        """Десериализация данных.

        ### Args:
        - serialized_data (`OrderedDict`): сериализованные данные
        - many (`bool`): Models queryset если True

        ### Returns:
        - `models.Model`: объект класса Model
        """
        if many:
            return deserialize('python', serialized_data)
        return next(deserialize('python', serialized_data)).object
