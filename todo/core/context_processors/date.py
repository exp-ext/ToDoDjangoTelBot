from datetime import date


def all_date(request):
    """Добавляет переменную с текущим годом и
    переменную с сегодняшней датой в index.html."""
    return {
        'year': date.today().year,
        'date_today': date.today()
    }
