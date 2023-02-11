from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self) -> str:
        return str(self.title)


class Post(models.Model):
    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Изложите свои мысли'
                  ' в этом поле и поделитесь ими с миром.'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='posts',
    )
    group = models.ForeignKey(
        Group,
        verbose_name='Группа поста',
        help_text='Каждый пост может относиться'
                  ' к некоторой группе или нет.',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'
        ordering = ["-pub_date"]

    def __str__(self):
        return str(self.text[:15])


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        verbose_name='Пост',
        help_text='Пост под которым оставляется комментарий',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='comments',
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Оставьте комментарий'
    )
    created = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
    )


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        User,
        verbose_name='Блогер',
        on_delete=models.CASCADE,
        related_name='following',
    )

    def __str__(self):
        return f'Подписка {self.user} на {self.auth}'
