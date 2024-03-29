from typing import Dict, List

from bleach import clean
from django.contrib.syndication.views import Feed as _Feed
from django.utils.feedgenerator import Rss201rev2Feed as FeedType

from .settings import TURBO_ALLOWED_ATTRS, TURBO_ALLOWED_TAGS


def sanitize_turbo(
        html: str,
        allowed_tags: List[str] = TURBO_ALLOWED_TAGS,
        allowed_attrs: Dict[str, List[str]] = TURBO_ALLOWED_ATTRS

) -> str:
    """Sanitizes HTML, removing not allowed tags and attributes.

    :param html:

    :param allowed_tags: List of allowed tags.
    :param allowed_attrs: Dictionary with attributes allowed for tags.

    """
    return clean(html, tags=allowed_tags, attributes=allowed_attrs, strip=True)


class YandexTurboFeedType(FeedType):

    def __init__(self, *args, **kwargs):

        self._analytics: list = kwargs.pop('ya_analytics', [])
        self._ads: list = kwargs.pop('ya_ads', [])

        super(YandexTurboFeedType, self).__init__(*args, **kwargs)

    def rss_attributes(self) -> dict:
        attrs = super(YandexTurboFeedType, self).rss_attributes()

        attrs.update({
            'xmlns:turbo': 'http://turbo.yandex.ru',
            'xmlns:yandex': 'http://news.yandex.ru',
        })

        return attrs

    def item_attributes(self, item: dict) -> dict:
        attrs = super(YandexTurboFeedType, self).item_attributes(item)

        if not item['ya_contents']:
            # No turbo content available.
            return attrs

        attrs.update({
            'turbo': 'true',
        })

        return attrs

    def add_root_elements(self, handler):
        super(YandexTurboFeedType, self).add_root_elements(handler)

        for params in self._analytics:
            handler.startElement('turbo:analytics', params)
            handler.endElement('turbo:analytics')

        for params in self._ads:
            handler.startElement('turbo:adNetwork', params)
            handler.endElement('turbo:adNetwork')

    def add_item_elements(self, handler, item):
        super(YandexTurboFeedType, self).add_item_elements(handler, item)

        # todo maybe
        # yandex:related

        extended = item['ya_extended_html']
        if extended:
            handler.addQuickElement('turbo:extendedHtml', extended)

        turbo_contents = item['ya_contents']

        if not turbo_contents:
            return

        handler.startElement('turbo:content', {})
        handler.ignorableWhitespace('<![CDATA[%s]]>' % turbo_contents)
        handler.endElement('turbo:content')

        source = item['ya_source']
        if source:
            handler.addQuickElement('turbo:source', source)

        topic = item['ya_topic']
        if topic:
            handler.addQuickElement('turbo:topic', topic)


class YandexTurboFeed(_Feed):
    """Yandex Turbo Pages Feed.

    .. code-block:: python

        from yaturbo import YandexTurboFeed

        class TurboFeed(YandexTurboFeed):
            '''
            More information on Django Syndication Feed Framework configuration:
            https://docs.djangoproject.com/en/2.0/ref/contrib/syndication/

            '''

            turbo_sanitize = True  # Let's strip HTML tags unsupported by Turbo pages.

            def item_turbo(self, item):
                return 'turbo contents'


        feed = TurboFeed()

        # configure Yandex Metrika counter
        feed.configure_analytics_yandex('123456789')

        # configure Yandex Advertisement Network
        feed.configure_ad_yandex('A-123', 'page-top')


        urlpatterns = [
            ...
            path('turbo/', feed),
            ...
        ]


    """
    feed_type = YandexTurboFeedType

    turbo_sanitize: bool = False
    """Whether to automatically sanitize HTML contents returned from `.item_turbo()`.

    Can be useful if you do not keep special HTML for Turbo pages.

    """

    def __init__(self):
        super(YandexTurboFeed, self).__init__()
        self.analytics: List[Dict] = []
        self.ads: List[Dict] = []

    def configure_ad_yandex(self, ident: str, turbo_id: str = ''):
        """Configure Yandex Advertisement Network.

        :param ident: Ad ID.

        :param turbo_id: ID of a place (figure) on Turbo page where to put an Ad block.

        """
        self.ads.append({
            'type': 'Yandex',
            'id': ident,
            'turbo-ad-id': turbo_id,
        })

    # todo maybe ad methods for
    # adfox

    def configure_analytics_yandex(self, ident: str, params: dict = None):
        """Configure Yandex Metrika analytics counter.

        :param ident: Metrika counter ID.

        :param params: Additional params.

        """
        params = params or {}

        data = {
            'type': 'Yandex',
            'id': ident,
        }

        if params:
            data['params'] = '%s' % params

        self.analytics.append(data)

    def configure_analytics_google(self, ident: str):
        """Configure Google Analytics counter.

        :param ident: Counter ID.

        """
        self.analytics.append({
            'type': 'Google',
            'id': ident,
        })

    def item_turbo(self, item) -> str:
        """This can be overridden to set turbo contents.

        :param item:

        """
        # todo maybe automatic html transform, e.g. with bleach
        return self.item_description(item)

    def item_turbo_source(self, item) -> str:
        """This can be overridden to set turbo source URL.

        Can be used with Yandex Metrika.

        :param item:

        """
        return ''

    def item_turbo_topic(self, item) -> str:
        """This can be overridden to set turbo page topic (title).

        Can be used with Yandex Metrika.

        :param item:

        """
        return ''

    def item_extra_kwargs(self, item) -> dict:
        kwargs = super(YandexTurboFeed, self).item_extra_kwargs(item)

        get_dyn = self._get_dynamic_attr

        contents = get_dyn('item_turbo', item)

        if contents and self.turbo_sanitize:
            contents = sanitize_turbo(contents)

        kwargs.update({
            'ya_contents': contents,
            'ya_source': get_dyn('item_turbo_source', item),
            'ya_topic': get_dyn('item_turbo_topic', item),
            'ya_extended_html': get_dyn('item_extended_html', item),
        })

        return kwargs

    def feed_extra_kwargs(self, obj) -> dict:
        kwargs = super(YandexTurboFeed, self).feed_extra_kwargs(obj)

        kwargs.update({
            'ya_analytics': self.analytics,
            'ya_ads': self.ads,
        })

        return kwargs
