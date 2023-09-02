from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm
from .models import Group, Post


def paginator(request, post_list):
    paginator = Paginator(post_list, settings.POST_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


def index(request):
    post_list = Post.objects.select_related('group', 'author')
    page_obj = paginator(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author')
    page_obj = paginator(request, post_list)
    context = {'group': group, 'posts': post_list, 'page_obj': page_obj, }
    return render(request, "posts/group_list.html", context)


def profile(request, username):
    author = get_object_or_404(get_user_model(), username=username)
    post_list = author.posts.select_related('group')
    count = post_list.count()
    page_obj = paginator(request, post_list)
    return render(
        request,
        'posts/profile.html',
        {
            'page_obj': page_obj,
            'count': count,
            'author': author,
        }
    )


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    return render(
        request,
        'posts/post_detail.html',
        {
            'post': post,
        }
    )


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    if not form.is_valid():
        return render(request, "posts/post_create.html", {"form": form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', request.user)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None, instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {'form': form, 'post': post, 'is_edit': True}
    return render(
        request, 'posts/post_edit.html', context)
