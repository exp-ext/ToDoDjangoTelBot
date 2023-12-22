from django import template

register = template.Library()


@register.filter
def addclass(field, css):
    """
    Фильтр Django для добавления CSS-класса к полю формы.

    ## Args:
        field (`django.forms.BoundField`): Поле формы, к которому нужно добавить CSS-класс.
        css (str): CSS-класс, который нужно добавить к полю формы.

    ## Returns:
        `django.forms.BoundField`: Поле формы с добавленным CSS-классом.

    ## Example:
        Использование в шаблоне Django:

        ```
        {{ form.field_name|addclass:"my-css-class" }}
        ```

        Где `form` - это экземпляр объекта формы, а `field_name` - имя поля в форме.

        Например, если у нас есть форма `MyForm` с полем `email` и мы хотим добавить CSS-класс "form-control" к этому полю,
        то мы можем использовать фильтр следующим образом:

        ```
        {{ form.email|addclass:"form-control" }}
        ```

        Этот фильтр преобразует поле формы в HTML-код, добавляя к нему указанный CSS-класс:

        ```html
        <input type="text" name="email" class="form-control" id="id_email">
        ```

        Теперь поле `email` будет иметь CSS-класс "form-control" для стилизации в соответствии с вашими потребностями.
    """
    return field.as_widget(attrs={'class': css})
