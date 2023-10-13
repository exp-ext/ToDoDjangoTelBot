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
        return Post.objects.all()

    def location(self, item):
        return reverse('posts:post_detail', args=[item.pk])

    def lastmod(self, item):
        return item.created_at
