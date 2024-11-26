from django.shortcuts import render
from django.views.generic import TemplateView


class AboutTemplateView(TemplateView):
    """Класс-представление для отображения страницы 'О проекте'."""
    template_name = 'pages/about.html'


class RulesTemplateView(TemplateView):
    """Класс-представление для отображения страницы 'Правила'."""
    template_name = 'pages/rules.html'


def csrf_failure(request, reason=''):
    """Функция обработки ошибки CSRF."""
    return render(request, 'pages/403csrf.html', status=403)


def page_not_found(request, exception):
    """Функция обработки ошибки 404 (Страница не найдена)."""
    return render(request, 'pages/404.html', status=404)


def server_error(request):
    """Функция обработки ошибки 500 (Ошибка на сервере)."""
    return render(request, 'pages/500.html', status=500)
