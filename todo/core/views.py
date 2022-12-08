import random
import secrets
import string
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
    character_set = string.digits + string.ascii_letters
    code = ''.join(secrets.choice(character_set) for i in range(length))
    return password
