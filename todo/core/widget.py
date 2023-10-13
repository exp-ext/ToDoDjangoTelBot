from datetime import datetime

import pytz
from django.forms import MultiWidget, TextInput
from django.utils.timezone import make_aware


class MinimalSplitDateTimeMultiWidget(MultiWidget):

    def __init__(self, widgets=None, attrs=None):
        if widgets is None:
            if attrs is None:
                attrs = {}
            date_attrs = attrs.copy()
            time_attrs = attrs.copy()

            date_attrs['type'] = 'date'
            time_attrs['type'] = 'time'

            widgets = [
                TextInput(attrs=date_attrs),
                TextInput(attrs=time_attrs),
            ]
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [value.date(), value.strftime('%H:%M')]
        return [None, None]

    def value_from_datadict(self, data, files, name):
        date_str, time_str = super().value_from_datadict(data, files, name)

        if date_str == time_str == '':
            return None

        if data.get('it_birthday'):
            time_str = '00:00'
            timezone = pytz.utc
        else:
            timezone = pytz.timezone(data.get('tz'))

        my_datetime = datetime.strptime(
            date_str + ' ' + time_str, "%Y-%m-%d %H:%M"
        )
        return make_aware(my_datetime, timezone)
