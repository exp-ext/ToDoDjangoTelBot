import re

from django import template

register = template.Library()


@register.filter(name='extract_first_paragraph_tag')
def extract_first_paragraph_tag(value):
    """
    Фильтр Django, который извлекает первый тег <p> из HTML-текста.

    ## Args:
        value (`str`): HTML-текст, из которого нужно извлечь первый тег <p>.

    ## Returns:
        `str`: Первый тег <p> из HTML-текста, если найден. В противном случае, возвращается исходный HTML-текст.

    ## Example:
        Использование в шаблоне Django:

        ```
        {{ html_text|extract_first_paragraph_tag }}
        ```

        Если `html_text` содержит следующий HTML-код:

        ```html
        <p>This is the first paragraph.</p>
        <p>This is the second paragraph.</p>
        ```

        Фильтр вернет:

        ```html
        <p>This is the first paragraph.</p>
        ```

        Если `html_text` не содержит тега <p>, то вернется исходный текст без изменений.
    """
    match = re.search(r'<p[^>]*>(.*?)<\/p>', value, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(0)
    return value
