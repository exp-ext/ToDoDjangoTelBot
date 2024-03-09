from core.models import Create
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_ckeditor_5.fields import CKEditor5Field
from sorl.thumbnail import ImageField


class Banner(Create):
    """Базовая модель баннера.

    ### Attributes:
    - title (`CharField`): Заголовок баннера.
    - image (`ImageField`): Путь к изображению баннера.
    - reference (`TextField`): Ссылка, на которую ведет баннер.
    - text (`CharField`): Слоган баннера.
    """
    title = models.CharField(_('заголовок'), max_length=100)

    image = ImageField(_('картинка'), upload_to='advertising/')
    reference = models.CharField(_('партнерская ссылка'), max_length=200)
    text = CKEditor5Field(_('слоган банера'), config_name='tasks')

    class Meta:
        ordering = ('-created_at',)
        abstract = True

    def __str__(self) -> str:
        return self.title


class PartnerBanner(Banner):
    """Модель для хранения информации о баннерах партнеров.

    ### Attributes:
    - title (`CharField`): Заголовок баннера.
    - image (`ImageField`): Путь к изображению баннера.
    - reference (`TextField`): Ссылка, на которую ведет баннер.
    - text (`CharField`): Слоган баннера.
    """

    class Meta:
        verbose_name = _('банер на сайте')
        verbose_name_plural = _('банеры на сайте')


class TelegramMailing(Banner):
    """Модель для организации телеграм-рассылок.

    ### Attributes:
    - title (`CharField`): Заголовок баннера.
    - image (`ImageField`): Путь к изображению баннера.
    - reference (`CharField`): Ссылка, на которую ведет баннер.
    - text (`TextField`): Слоган рассылки.
    - target (`str`): Цель рассылки, выбирается из списка вариантов.
    - remind_at (`datetime`): Время срабатывания рассылки.

    """

    class Targets(models.TextChoices):
        """Варианты целей рассылки."""
        USERS = 'u', _('все пользователи')
        GROUPS = 'g', _('все группы')

    reference = models.CharField(_('партнерская ссылка'), max_length=200, blank=True, null=True)
    target = models.CharField(_('получатели'), max_length=1, choices=Targets.choices, default=Targets.USERS)
    remind_at = models.DateTimeField(_('время срабатывания'))

    class Meta:
        verbose_name = _('телеграмм рассылка')
        verbose_name_plural = _('телеграмм рассылки')


class AdvertisementWidget(Create):
    """Модель для скриптов рекламы.

    ### Attributes:
    - title (`CharField`): Краткое описание скрипта.
    - script(`TextField`): Скрипт из конструктора виджетов ЯМ.
    - type(): форма скрипта

    """
    class Form(models.TextChoices):
        """Варианты целей рассылки."""
        LINE = 'l', _('линейная форма')
        SQUARE = 's', _('квадратная форма')

    title = models.CharField(_('описание'), max_length=100)
    advertiser = models.CharField(_('рекламодатель'), max_length=100)
    script = models.TextField(_('скрипт для отображения в станице'))
    form = models.CharField(_('тип виджета'), max_length=1, choices=Form.choices, default=Form.LINE)

    class Meta:
        verbose_name = _('скрипт рекламного виджета')
        verbose_name_plural = _('скрипты рекламных виджетов')
        ordering = ('-created_at',)

    def __str__(self) -> str:
        return self.title


class MyBanner(Banner):
    """Модель для хранения информации о баннерах партнеров.

    ### Attributes:
    - title (`CharField`): Заголовок баннера.
    - image (`ImageField`): Путь к изображению баннера.
    - reference (`TextField`): Ссылка, на которую ведет баннер.
    - text (`CharField`): Слоган баннера.
    - mobile_text (`CharField`): Слоган баннера для мобильной версии.
    """
    mobile_text = CKEditor5Field(_('слоган банера для мобильной версии'), config_name='extends')

    class Meta:
        verbose_name = _('мой банер на сайте')
        verbose_name_plural = _('мои банеры на сайте')
