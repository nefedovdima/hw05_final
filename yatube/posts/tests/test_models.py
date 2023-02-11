from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост длиной более 15 символов',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        modelobj_expected_names = {
            PostModelTest.post: 'Тестовый пост д',
            PostModelTest.group: 'Тестовая группа',
        }
        for modelobj, expected_name in modelobj_expected_names.items():
            with self.subTest(modelobj=modelobj):
                self.assertEqual(expected_name, str(modelobj))

    def test_verbose_name(self):
        """Проверяем расширенные имена модели Post"""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа поста',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_help_text(self):
        """Проверяем подсказки для полей модели Post"""
        post = PostModelTest.post
        field_help_text = {
            'text': 'Изложите свои мысли'
                    ' в этом поле и поделитесь ими с миром.',
            'group': 'Каждый пост может относиться'
                     ' к некоторой группе или нет.',
        }
        for field, expected_value in field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)
