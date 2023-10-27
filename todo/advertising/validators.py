from django.core.exceptions import ValidationError


def validate_hour_multiple(value):
    if value.minute != 0 or value.second != 0:
        raise ValidationError('Выберите или введите время, кратное часу.')
