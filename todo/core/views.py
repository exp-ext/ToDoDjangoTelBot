import random

from django.shortcuts import render


def page_not_found(request, exception):
    return render(request, 'core/404.html', {'path': request.path}, status=404)


def server_error(request):
    return render(request, 'core/500.html', status=500)


def permission_denied(request, exception):
    return render(request, 'core/403.html', status=403)


def csrf_failure(request, reason=''):
    return render(request, 'core/403csrf.html')


def get_password(length):
    """
    Password Generator:
    length - password length
    """
    chars = ('+-*!$=@abcdefghijklnopqrstuvwxyz'
             'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890')
    length = int(length)
    password = ''
    for i in range(length):
        password += random.choice(chars)
    return password
