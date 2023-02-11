from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page


from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from .utils import pagination


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.select_related('group')
    page_obj = pagination(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    template = 'posts/index.html'
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = pagination(request, posts)
    context = {
        'page_obj': page_obj,
        'group': group,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=user)
    post_count = posts.count()
    page_obj = pagination(request, posts)
    following = (Follow.objects.
                 filter(user=request.user).
                 filter(author=user).exists())
    context = {
        'author': user,
        'page_obj': page_obj,
        'post_count': post_count,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    context = {'form': form}
    if not form.is_valid():
        return render(request, 'posts/create_post.html', context)
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', post.author)


@login_required
def post_edit(request, post_id):
    edit_post = get_object_or_404(Post, id=post_id)
    is_edit = True
    template = 'posts/create_post.html'
    if request.user != edit_post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None,
                    instance=edit_post,
                    files=request.FILES or None)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    post_id = edit_post.pk
    return render(request,
                  template,
                  {'form': form, 'is_edit': is_edit, 'post_id': post_id})


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm()
    comments = post.comments.all()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.select_related('author').filter(
        author__following__user=request.user)
    page_obj = pagination(request, posts)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    '''Подписка на блогера'''
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):
    '''Отписка от блогера'''
    follow = get_object_or_404(Follow,
                               user=request.user,
                               author__username=username)
    follow.delete()
    return redirect("posts:profile", username=username)
