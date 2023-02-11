from django.test import TestCase, Client
from django.conf import settings
from django.urls import reverse
from django import forms
from django.core.cache import cache

from ..models import Group, Post, User


class PostViewsTests(TestCase):
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
        cls.page_names_templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': cls.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': cls.post.author.username}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': cls.post.id}):
            'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': cls.post.id}):
            'posts/create_post.html',
            reverse('posts:post_create'):
            'posts/create_post.html'
        }

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create_user(username='noauth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(PostViewsTests.user)

    def test_pages_use_correct_templates_inviews(self):
        '''Проверяется, что URL-адресам соответствуют правильные шаблоны'''
        for page_name, template in PostViewsTests.page_names_templates.items():
            with self.subTest(page_name=page_name):
                response = self.authorized_client_author.get(page_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client_author.get(reverse('posts:index'))
        first_post = response.context['page_obj'][0]
        group_title_0 = first_post.group.title
        post_text_0 = first_post.text
        self.assertEqual(group_title_0, self.group.title)
        self.assertEqual(post_text_0, self.post.text)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        group_list_url = reverse('posts:group_list',
                                 kwargs={'slug': self.group.slug})
        response = self.authorized_client.get(group_list_url)
        first_post = response.context['page_obj'][0]
        post_group_0 = first_post.group.title
        self.assertEqual(post_group_0, PostViewsTests.group.title)
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        profile_url = reverse('posts:profile',
                              kwargs={'username': self.post.author.username})
        response = self.authorized_client.get(profile_url)
        first_post = response.context['page_obj'][0]
        post_group_0 = first_post.author
        self.assertEqual(post_group_0, PostViewsTests.post.author)
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk}))
        first_post = response.context['post']
        self.assertEqual(first_post.pk, PostViewsTests.post.pk)

    def test_edit_show_correct_context(self):
        """Шаблон edit сформирован с правильным контекстом."""
        response = self.authorized_client_author.get(
            reverse('posts:post_edit', kwargs={'post_id':
                    self.post.id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_create_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_on_pages(self):
        '''Проверяется, что если при создании поста указать группу,
            то этот пост появляется
            -на главной странице сайта,
            -на странице выбранной группы,
            -в профайле пользователя.'''
        pages = [reverse('posts:index'),
                 reverse('posts:group_list',
                         kwargs={'slug': PostViewsTests.group.slug}),
                 reverse('posts:profile',
                         kwargs={'username': self.post.author.username})]
        for page in pages:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                form_field = response.context['page_obj']
                self.assertIn(PostViewsTests.post, form_field)

    def test_index_cach(self):
        '''Проверяется кеширование страницы index'''
        post = Post.objects.create(
            text='Новый пост',
            author=self.post.author
        )
        post_create = self.guest_client.get(reverse('posts:index'))
        post.delete()
        post_delete = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(post_create.content, post_delete.content)

        cache.clear()
        post_after_cach_clear = self.guest_client.get(reverse('posts:index'))
        self.assertNotEqual(post_create.content, post_after_cach_clear.content)


class PaginatorViewsTest(TestCase):
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
        objs = (Post(text=f'Тестовый текст {i}',
                     author=cls.user, group=cls.group)
                for i in range(settings.POSTS_PER_PAGE + 2))
        Post.objects.bulk_create(objs, batch_size=12)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create_user(username='newauth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.pages = [reverse('posts:index'),
                      reverse('posts:group_list',
                              kwargs={'slug':
                                      PaginatorViewsTest.group.slug}),
                      reverse('posts:profile',
                              kwargs={'username':
                                      PaginatorViewsTest.
                                      post.author.username})]

    def test_first_page_contains_ten_records(self):
        for page in self.pages:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertEqual(len(response.context['page_obj']),
                                 settings.POSTS_PER_PAGE)

    def test_second_page_contains_three_records(self):
        for page in self.pages:
            with self.subTest(page=page):
                response = self.authorized_client.get(page + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)
