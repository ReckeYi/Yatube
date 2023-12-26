from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Post, Group, User, Comment

@cache_page(60 * 15)
def index(request):
    title = 'Группы проекта'
    # Одна строка вместо тысячи слов на SQL:
    # в переменную posts будет сохранена выборка из 10 объектов модели Post,
    # отсортированных по полю pub_date по убыванию (от больших значений к меньшим)
    # posts = Post.objects.order_by('-pub_date')[:10]
    post_list = Post.objects.all().order_by('-pub_date')
    # Если порядок сортировки определен в классе Meta модели,
    # запрос будет выглядеть так:
    # post_list = Post.objects.all()
    # Показывать по 10 записей на странице.
    paginator = Paginator(post_list, 10)

    # Из URL извлекаем номер запрошенной страницы - это значение параметра page
    page_number = request.GET.get('page')

    # Получаем набор записей для страницы с запрошенным номером
    page_obj = paginator.get_page(page_number)
    # Отдаем в словаре контекста

    # В словаре context отправляем информацию в шаблон
    context = {
        "page_obj": page_obj,
    }
    template = 'posts/index.html'
    return render(request, template, context)


def group_posts(request, slug):
    # Функция get_object_or_404 получает по заданным критериям объект
    # из базы данных или возвращает сообщение об ошибке, если объект не найден.
    # В нашем случае в переменную group будут переданы объекты модели Group,
    # поле slug у которых соответствует значению slug в запросе
    group = get_object_or_404(Group, slug=slug)

    # Метод .filter позволяет ограничить поиск по критериям.
    # Это аналог добавления
    # условия WHERE group_id = {group_id}
    # posts = Post.objects.filter(group=group).order_by('-pub_date')[:10]
    post_list = Post.objects.all().order_by('-pub_date')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "group": group,
        "page_obj": page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    # Здесь код запроса к модели и создание словаря контекста
    user_obj = get_object_or_404(User, username=username)
    user_post_list = Post.objects.filter(author=user_obj).order_by('-pub_date')
    paginator = Paginator(user_post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "user_obj": user_obj,
        "user_post_list": user_post_list,
        "page_obj": page_obj
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    amount_posts = Post.objects.filter(author=post.author).count()
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post=post_id)
    context = {
        "post": post,
        "amount_posts": amount_posts,
        "form": form,
        "comments": comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )

    if request.method == "POST" and form.is_valid():
        temp_form = form.save(commit=False)
        temp_form.author = request.user
        temp_form.save()
        return redirect("posts:profile", temp_form.author)

    context = {
        "form": form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    is_edit = Post.objects.get(id=post_id)

    if request.user != is_edit.author:
        return redirect("posts:post_detail", post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=is_edit,
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id)

    context = {
        "form": form,
        "is_edit": is_edit,
    }
    return render(request, "posts/create_post.html", context)

@login_required
def add_comment(request, post_id):
    post = Post.objects.get(id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect("posts:post_detail", post_id=post_id)

