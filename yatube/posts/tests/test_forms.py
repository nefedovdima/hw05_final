import shutil
import tempfile

from http import HTTPStatus
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.core.cache import cache

from ..models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост',
        )
        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                     b'\x01\x00\x80\x00\x00\x00\x00\x00'
                     b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                     b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                     b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                     b'\x0A\x00\x3B')
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create_user(username='noauth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(PostFormsTests.user)

    def test_create_post(self):
        '''При отправке валидной формы со страницы создания поста
         создаётся новая запись в базе данных'''
        Post.objects.all().delete()
        post_count = Post.objects.count()
        form_data = {
            'text': 'Новый пост',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        first_element = Post.objects.first()
        self.assertEqual(first_element.text, form_data['text'])
        self.assertEqual(first_element.group.id, form_data['group'])
        self.assertEqual(first_element.author, self.user)

    def test_form_edits_post(self):
        '''При отправке валидной формы со страницы редактирования поста
         происходит изменение поста с post_id в базе данных'''
        form_data = {
            'text': 'Новый пост',
            'group': self.group.id
        }
        posts_count = Post.objects.count()
        response = self.authorized_client_author.post(
            reverse('posts:post_edit', kwargs={
                    'post_id': self.post.id}),
            data=form_data,
            follow=True)
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={'post_id': self.post.id}))

        self.assertEqual(Post.objects.count(), posts_count)
        database_post = Post.objects.get(id=self.post.id)
        self.assertEqual(database_post.text, form_data['text'])
        self.assertEqual(database_post.group.id, form_data['group'])
        self.assertEqual(database_post.author, PostFormsTests.user)

    def test_image_form_create_post(self):
        '''При отправке поста с картинкой
        через форму PostForm создаётся запись в базе данных'''
        Post.objects.all().delete()
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тест',
            'image': self.image,
            'group': self.group.id
        }
        response = self.authorized_client_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        post = Post.objects.first()
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertRedirects(response, reverse('posts:profile',
                             kwargs={'username':
                                     self.post.author.username}))
        self.assertEqual(post.text, form_data['text'],
                         'Текст поста не совпадает')
        self.assertEqual(post.group.id, form_data['group'],
                         'Группа не совпадает')
        self.assertEqual(post.author, self.post.author,
                         'Автор не совпадает')
        self.assertEqual(post.image, f'posts/{self.image.name}',
                         'Картинка не совпадает')
