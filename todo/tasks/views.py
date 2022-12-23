from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProfileForm

User = get_user_model()


@login_required
def accounts_profile(request: HttpRequest, username: str):
    """Профиль юзера."""
    user = get_object_or_404(User, username=username)

    if user != request.user:
        redirect('index')

    form = ProfileForm(
        request.POST or None,
        files=request.FILES or None,
        instance=user
    )

    if request.method == "POST" and form.is_valid():
        user = form.save()
        return redirect('tasks:accounts_profile', username=username)

    context = {
        'user': user,
        'form': form,
    }
    template = 'tasks/accounts_profile.html'
    return render(request, template, context)
