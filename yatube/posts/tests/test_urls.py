from http import HTTPStatus
from django.test import TestCase, Client
from django.urls import reverse

from ..models import Group, Post, User


class PostURLTests(TestCase):
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
        self.guest_client = Client()
        self.user = User.objects.create_user(username='noauth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(PostURLTests.user)

    def test_urls_exists_at_desired_location_for_anonymous(self):
        urls_docs = {
            reverse('posts:index'): """Страница /
             доступна любому пользователю.""",
            reverse('posts:group_list', kwargs={'slug':
                                                PostURLTests.group.slug}):
            """Страница /group/<slug> доступна любому пользователю.""",
            reverse('posts:post_detail',
                    kwargs={'post_id':
                            PostURLTests.post.id}):
            """Страница /posts/<post_id>/ доступна любому пользователю.""",
        }
        for url, doc in urls_docs.items():
            with self.subTest(url=url):
                self.__doc__ = doc
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_post_id_edit_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /posts/<post_id>/edit/ перенаправит анонимного
        пользователя на страницу логина."""
        posts_post_id_edit_url = reverse('posts:post_edit', kwargs={'post_id':
                                         PostURLTests.post.id})
        response = self.guest_client.get(posts_post_id_edit_url,
                                         follow=True)
        self.assertRedirects(response, f'/auth/login/?next='
                             f'{posts_post_id_edit_url}')

    def test_post_id_edit_url_exists_for_author(self):
        """Страница /posts/<post_id>/edit/ доступна для автора поста."""
        posts_post_id_edit_url = reverse('posts:post_edit', kwargs={'post_id':
                                         PostURLTests.post.id})
        response = self.authorized_client_author.get(posts_post_id_edit_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_id_edit_url_not_exists_for_noauthor(self):
        """Страница /posts/<post_id>/edit/ недоступна для авторизованного
        пользователя,который не является автором поста."""
        posts_post_id_edit_url = reverse('posts:post_edit', kwargs={'post_id':
                                         PostURLTests.post.id})
        response = self.authorized_client.get(posts_post_id_edit_url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_create_url_not_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /create/ перенаправит анонимного
        пользователя на страницу логина."""
        create_url = reverse('posts:post_create')
        response = self.guest_client.get(create_url,
                                         follow=True)
        self.assertRedirects(response, f'/auth/login/?next='
                             f'{create_url}')

    def test_create_url_exists_for_authorized(self):
        """Страница /create/ доступна для авторизованного пользователя."""
        create_url = reverse('posts:post_create')
        response = self.authorized_client.get(create_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page_url_exists_for_authorized(self):
        """Обращение к unexisting_page/ выдает ошибку NOT FOUND."""
        response = self.guest_client.get('unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_pages_use_correct_templates(self):
        '''Проверяется, что unexisting_page/
        соответствует шаблон core/404.html'''
        page_name = 'unexisting_page/'
        response = self.authorized_client_author.get(page_name)
        template = 'core/404.html'
        self.assertTemplateUsed(response, template)
