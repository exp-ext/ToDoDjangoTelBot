from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from posts.models import Post


class StaticViewSitemap(Sitemap):
    priority = 0.9
    changefreq = 'daily'

    def items(self):
        return ['index', 'about:support']

    def location(self, item):
        return reverse(item)


class DynamicViewSitemap(Sitemap):
    priority = 0.9
    changefreq = 'daily'

    def items(self):
        return Post.objects.filter(moderation='PS')

    def location(self, item):
        return reverse('posts:post_detail', args=[item.slug])

    def lastmod(self, item):
        return item.updated_at
