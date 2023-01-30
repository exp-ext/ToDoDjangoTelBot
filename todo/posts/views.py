from core.views import paginator_handler
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from users.models import Group

from .forms import CommentForm, PostForm
from .models import Follow, Post

User = get_user_model()


def search(request):
    keyword = request.GET.get("q", "")

    if not keyword:
        return redirect('posts:index_posts')

    post_list = (
        Post.objects
        .filter(text__contains=keyword)
        .order_by('group')
        .select_related('author', 'group')
    )
    page_obj = paginator_handler(request, post_list)

    context = {
        'page_obj': page_obj,
        'keyword': keyword,
        'post_list': post_list,
    }
    template = 'posts/search_result.html'
    return render(request, template, context)


def index_posts(request):
    post_list = (
        Post.objects
        .all()
        .select_related('author', 'group')
    )

    page_obj = paginator_handler(request, post_list)

    context = {
        'page_obj': page_obj,
    }
    template = 'posts/index_posts.html'
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)

    post_list = group.posts.all()

    page_obj = paginator_handler(request, post_list)

    context = {
        'group': group,
        'page_obj': page_obj,
    }
    template = 'posts/group_list.html'
    return render(request, template, context)


def profile(request, username):
    user = get_object_or_404(User, username=username)

    user_posts = user.posts.select_related('group')

    page_obj = paginator_handler(request, user_posts)

    posts_count = page_obj.paginator.count

    following = False

    if request.user.is_authenticated:
        following = request.user.follower.filter(author=user).exists()

    context = {
        'author': user,
        'page_obj': page_obj,
        'posts_count': posts_count,
        'following': following,
    }
    template = 'posts/profile.html'
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related('author'),
        pk=post_id
    )
    authors_posts_count = post.author.posts.count()

    comments = post.comments.all()

    form = CommentForm(request.POST or None)

    context = {
        'post': post,
        'authors_posts_count': authors_posts_count,
        'comments': comments,
        'form': form,
    }
    template = 'posts/post_detail.html'
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )

    if request.method == "POST" and form.is_valid():
        form = form.save(commit=False)
        form.author = request.user
        form.save()
        return redirect(
            'posts:profile',
            username=request.user.username
        )

    context = {
        'form': form,
    }
    template = 'posts/create_post.html'
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if request.method == "POST" and form.is_valid():
        post = form.save()
        return redirect('posts:post_detail', post_id=post_id)

    is_edit = True
    context = {
        'form': form,
        'is_edit': is_edit,
    }
    template = 'posts/create_post.html'
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    form = CommentForm(request.POST or None)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = (
        Post.objects.
        filter(author__following__user=request.user).
        prefetch_related('group')
    )

    page_obj = paginator_handler(request, post_list)

    context = {
        'page_obj': page_obj,
    }
    template = 'posts/follow.html'
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author == request.user:
        post.delete()
    return redirect('posts:profile', post.author.username)
