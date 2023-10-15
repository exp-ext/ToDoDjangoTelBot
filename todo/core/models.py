from django.db import models


class Create(models.Model):
    """
    Абстрактная модель, предоставляющая поле 'created_at' для фиксации времени создания объекта.

    ### Fields:
    - created_at (`DateTimeField`): Дата и время создания объекта.

    ### Meta:
    - abstract = True: Это абстрактная модель, не будет создавать таблицу в базе данных.
    - ordering = ('-created_at',): Сортировка объектов по убыванию времени создания.

    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        abstract = True
        ordering = ('-created_at',)


class CreateUpdater(Create):
    """
    Абстрактная модель, предоставляющая поле 'updated_at' для фиксации времени обновления объекта.

    ### Fields:
    - updated_at (`DateTimeField`): Дата и время последнего обновления объекта.

    ### Meta:
    - abstract = True: Это абстрактная модель, не будет создавать таблицу в базе данных.
    - ordering = ('-created_at',): Сортировка объектов по убыванию времени создания.

    """
    updated_at = models.DateTimeField(auto_now=True)

    class Meta(Create.Meta):
        abstract = True
