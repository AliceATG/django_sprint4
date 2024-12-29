from django.shortcuts import get_object_or_404, redirect
from blog.models import Post, Category, Comment
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.urls import reverse
from django.views.generic import (CreateView, DeleteView, ListView, UpdateView,
                                  DetailView, View)
from .forms import PostForm, CommentForm, ProfileEditForm
from django.contrib.auth import get_user_model
from django.http import Http404

User = get_user_model()

POSTS_PAGIN = 10


def get_post_data(kwargs):
    """Получить объект Post из базы данных по параметрам."""
    return get_object_or_404(
        Post,
        pk=kwargs['post_id'],
        pub_date__lte=timezone.now(),
        is_published=True,
        category__is_published=True,
    )


def check_author_permission(instance, user):
    """Проверить, является ли пользователь автором объекта."""
    return instance.author == user


class PostMixin:
    """Базовый класс для работы с моделями постов."""

    model = Post
    template_name = 'blog/create.html'


class PostCreateView(PostMixin, LoginRequiredMixin, CreateView):
    """
    Класс для создания нового поста.
    - При успешном сохранении поста, автором указывается текущий пользователь.
    - После создания перенаправляет на профиль автора.
    """

    form_class = PostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("blog:profile", args=[self.request.user])


class PostUpdateView(PostMixin, LoginRequiredMixin, UpdateView):
    """
    Класс для редактирования существующего поста. Требует авторизации.
    - Позволяет редактировать пост только его автору.
    - После обновления перенаправляет на страницу деталей поста.
    """

    form_class = PostForm
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if not check_author_permission(post, request.user):
            return redirect('blog:post_detail', id=self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'id':
                                                   self.kwargs['post_id']})


class PostDeleteView(PostMixin, LoginRequiredMixin, DeleteView):
    """
    Класс для удаления поста. Требует авторизации.
    - Удалять пост может только его автор.
    - После удаления перенаправляет на профиль автора.
    """

    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if not check_author_permission(post, request.user):
            return redirect('blog:post_detail', id=self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = PostForm(instance=self.object)
        return context

    def get_success_url(self):
        return reverse("blog:profile", kwargs={"username": self.request.user})


class IndexListView(ListView):
    """
    Класс для отображения списка всех опубликованных постов.
    - Пагинация по 10 постов на страницу.
    - Посты сортируются по дате публикации.
    """

    model = Post
    paginate_by = POSTS_PAGIN
    template_name = 'blog/index.html'

    def get_queryset(self):
        return (
            self.model.objects.select_related('location', 'author', 'category')
            .filter(is_published=True,
                    category__is_published=True,
                    pub_date__lte=timezone.now())
            .annotate(comment_count=Count("comment"))
            .order_by("-pub_date"))


class ProfileListView(ListView):
    """
    Класс для отображения профиля пользователя и его постов.
    - Пагинация по 10 постов на страницу.
    - Выводит информацию о пользователе, чей профиль отображается.
    """

    model = Post
    paginate_by = POSTS_PAGIN
    template_name = 'blog/profile.html'

    def get_queryset(self):
        return (
            self.model.objects.select_related('author')
            .filter(author__username=self.kwargs['username'])
            .annotate(comment_count=Count("comment"))
            .order_by("-pub_date"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(
            User,
            username=self.kwargs['username'])
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """
    Класс для редактирования профиля текущего пользователя.
    - Позволяет обновить данные профиля.
    - После сохранения перенаправляет обратно на страницу профиля.
    """

    template_name = 'blog/user.html'
    form_class = ProfileEditForm

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse("blog:profile", args=[self.request.user])


class PostDetailView(DetailView):
    """
    Класс для отображения деталей поста.
    - Проверяет доступность поста.
    - Если пост недоступен, и пользователь не является автором,
      выдаёт ошибку 404.
    - Выводит форму для добавления комментариев и список комментариев к посту.
    """

    model = Post
    template_name = 'blog/detail.html'

    def get_object(self, queryset=None):
        post = get_object_or_404(self.model, pk=self.kwargs['id'])
        if (not post.is_published or not post.category.is_published
                or post.pub_date > timezone.now()):
            if self.request.user != post.author:
                raise Http404("Пост недоступен")

        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comment.select_related('author')
        return context


class CategoryPostsListView(ListView):
    """
    Класс для отображения постов определённой категории.
    - Проверяет, опубликована ли категория.
    - Пагинация по 10 постов на страницу.
    - Сортирует посты по дате публикации.
    """

    model = Post
    paginate_by = POSTS_PAGIN
    template_name = 'blog/category.html'

    def get_queryset(self):
        category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True)

        return (
            category.post.select_related('location', 'author', 'category')
            .filter(is_published=True,
                    pub_date__lte=timezone.now())
            .annotate(comment_count=Count("comment"))
            .order_by("-pub_date"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(
            Category.objects.values('id', 'title', 'description'),
            slug=self.kwargs['category_slug'])
        return context


class CommentCreateView(LoginRequiredMixin, CreateView):
    """
    Класс для создания нового комментария. Требует авторизации.
    - Привязывает комментарий к текущему пользователю и посту.
    - После успешного создания перенаправляет на страницу деталей поста.
    """

    model = Comment
    form_class = CommentForm
    template_name = "blog/comment.html"
    post_obj = None

    def dispatch(self, request, *args, **kwargs):
        self.post_obj = get_post_data(kwargs)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.post_obj
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("blog:post_detail",
                       kwargs={'id': self.kwargs['post_id']})


class CommentMixin(LoginRequiredMixin, View):
    """
    Базовый класс для работы с комментариями.
    - Проверяет, что текущий пользователь является автором комментария.
    - Если пользователь не автор, перенаправляет на страницу деталей поста.
    """

    model = Comment
    template_name = "blog/comment.html"
    pk_url_kwarg = "comment_id"

    def dispatch(self, request, *args, **kwargs):
        comment = get_object_or_404(
            Comment,
            pk=kwargs['comment_id'],
        )
        if not check_author_permission(comment, request.user):
            return redirect('blog:post_detail', id=kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("blog:post_detail",
                       kwargs={'id': self.kwargs['post_id']})


class CommentUpdateView(CommentMixin, UpdateView):
    """Класс для редактирования комментария."""

    form_class = CommentForm


class CommentDeleteView(CommentMixin, DeleteView):
    """Класс для удаления комментария."""

    pass
