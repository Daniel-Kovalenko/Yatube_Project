from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class PostTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_name1',
                                              email='test1@mail.ru',
                                              password='test_pass')
        cls.group = Group.objects.create(
            title='Заголовок для 1 тестовой группы',
            slug='test_slug1')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовая запись для создания 1 поста',
            group=cls.group)
        cls.author = User.objects.create_user(username='test_name2',
                                              email='test2@mail.ru',
                                              password='test_pass')
        cls.group = Group.objects.create(
            title='Заголовок для 2 тестовой группы',
            slug='test_slug2')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовая запись для создания 2 поста',
            group=cls.group)
        cls.user = User.objects.create_user(username='YourBestFriend')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def standart_post_check(self, post):
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author.username, self.post.author.username)
        self.assertEqual(post.group.title, self.post.group.title)
        self.assertEqual(self.post.author.username, 'test_name2')

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/post_create.html': reverse('posts:post_create'),
            'posts/group_list.html': (
                reverse('posts:group_list', kwargs={'slug': 'test_slug2'})
            ),
        }
        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_pages_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context["page_obj"][0]
        self.standart_post_check(post)

    def test_group_pages_show_correct_context(self):
        """Шаблон группы"""
        response = self.authorized_client.get(reverse
                                              ('posts:group_list',
                                               kwargs={'slug': 'test_slug2'}))
        group = response.context["group"]
        self.assertEqual(group.title, 'Заголовок для 2 тестовой группы')
        self.assertEqual(group.slug, 'test_slug2')
        post = response.context["page_obj"][0]
        self.standart_post_check(post)

    def test_post_another_group(self):
        """Пост не попал в другую группу"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug1'}))
        post = response.context["page_obj"][0]
        post_text_0 = post.text
        self.assertTrue(post_text_0, 'Тестовая запись для создания 2 поста')

    def test_new_post_show_correct_context(self):
        """Шаблон сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'test_name2'}))
        post = response.context["page_obj"][0]
        self.standart_post_check(post)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create_user(username='test_name',
                                              email='test@mail.ru',
                                              password='test_pass',)
        cls.group = Group.objects.create(
            title=('Заголовок для тестовой группы'),
            slug='test_slug2',
            description='Тестовое описание')
        cls.posts = []
        for i in range(13):
            cls.posts.append(Post(
                text=f'Тестовый пост {i}',
                author=cls.author,
                group=cls.group
            )
            )
        Post.objects.bulk_create(cls.posts)
        cls.user = User.objects.create_user(username='test_name11')
        cls.list_urls = [
            reverse("posts:index"),
            reverse("posts:group_list",
                    kwargs={"slug": "test_slug2"}),
            reverse("posts:profile",
                    kwargs={"username": "test_name"}),
        ]

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_posts(self):
        for tested_url in self.list_urls:
            response = self.client.get(tested_url)
            self.assertEqual(len(response.context.get('page_obj')),
                             settings.POST_LIMIT)

    def test_second_page_contains_three_posts(self):
        for tested_url in self.list_urls:
            tested_url += '?page=2'
            response = self.client.get(tested_url)
            self.assertEqual(len(response.context.get('page_obj')),
                             settings.POST_LIMIT_2_PAGE)
