from django import forms
from django.contrib.auth import get_user_model
from .models import Comment, Post

User = get_user_model()


class PostForm(forms.ModelForm):
    """Форма для создания и редактирования постов."""
    class Meta:
        model = Post
        fields = ('title', 'text', 'pub_date', 'category', 'location', 'image')
        widgets = {
            'pub_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}),
        }


class CommentForm(forms.ModelForm):
    """Форма для создания и редактирования комментариев."""
    class Meta:
        model = Comment
        fields = ('text',)


class ProfileEditForm(forms.ModelForm):
    """Форма для создания и редактирования профиля пользователя."""
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')
