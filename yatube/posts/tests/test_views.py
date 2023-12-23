import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="TestName")

        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        cls.group_another = Group.objects.create(
            title="Другая тестовая группа",
            slug="test-slug-another",
            description="Тестовое описание другой группы",
        )

        cls.post = Post.objects.create(
            text="Тестовый текст",
            author=cls.user,
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_pages_uses_correct_template(self):
        templates_pages_names = {
            reverse("posts:index"): "posts/index.html",
            reverse(
                "posts:group_list", args=[PostPagesTests.group.slug]
            ): "posts/group_list.html",
            reverse(
                "posts:profile",
                args=[PostPagesTests.user],
            ): "posts/profile.html",
            reverse(
                "posts:post_detail", args=[PostPagesTests.post.id]
            ): "posts/post_detail.html",
            reverse(
                "posts:post_edit",
                args=[PostPagesTests.post.id],
            ): "posts/create_post.html",
            reverse("posts:post_create"): "posts/create_post.html",
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = PostPagesTests.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def context_verification_method(self, response, variable, flag=False):
        if flag:
            self.assertEqual(
                response.context[variable][0].id,
                PostPagesTests.post.id,
            )
            self.assertEqual(
                response.context[variable][0].text,
                PostPagesTests.post.text,
            )
            self.assertEqual(
                response.context[variable][0].author.username,
                PostPagesTests.post.author.username,
            )
            self.assertEqual(
                response.context[variable][0].group.title,
                PostPagesTests.post.group.title,
            )
        else:
            self.assertEqual(
                response.context.get(variable).text,
                PostPagesTests.post.text,
            )
            self.assertEqual(
                response.context.get(variable).author.username,
                PostPagesTests.post.author.username,
            )
            self.assertEqual(
                response.context.get(variable).group.title,
                PostPagesTests.post.group.title,
            )

    def test_pages_index_group_profile_show_correct_context(self):
        responses = [
            PostPagesTests.authorized_client.get(reverse("posts:index")),
            PostPagesTests.authorized_client.get(
                reverse(
                    "posts:group_list",
                    args=[PostPagesTests.group.slug],
                )
            ),
            PostPagesTests.authorized_client.get(
                reverse("posts:profile", args=[PostPagesTests.user])
            ),
        ]
        for response in responses:
            with self.subTest(response=response):
                PostPagesTests.context_verification_method(
                    self,
                    response,
                    "page_obj",
                    True,
                )

    def test_post_detail_page_show_correct_context(self):
        response = PostPagesTests.authorized_client.get(
            reverse("posts:post_detail", args=[PostPagesTests.post.id])
        )
        PostPagesTests.context_verification_method(self, response, "post")

    def test_group_posts_page_show_correct_context(self):
        response = PostPagesTests.authorized_client.get(
            reverse("posts:group_list", args=[PostPagesTests.group.slug]),
        )
        self.assertEqual(
            response.context.get("group").title,
            PostPagesTests.group.title,
        )
        self.assertEqual(
            response.context.get("group").slug,
            PostPagesTests.group.slug,
        )
        self.assertEqual(
            response.context.get("group").description,
            PostPagesTests.group.description,
        )

    def test_profile_page_show_correct_context(self):
        response = PostPagesTests.authorized_client.get(
            reverse("posts:profile", args=[PostPagesTests.user])
        )
        self.assertEqual(
            response.context.get("user_obj").username,
            PostPagesTests.user.username,
        )

    def test_pages_post_create_post_edit_show_correct_context(self):
        response_create = PostPagesTests.authorized_client.get(
            reverse("posts:post_create")
        )
        response_edit = PostPagesTests.authorized_client.get(
            reverse(
                "posts:post_edit",
                args=[PostPagesTests.post.id],
            )
        )
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response_create.context.get(
                    "form",
                ).fields.get(value)
                self.assertIsInstance(form_field, expected)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response_edit.context.get(
                    "form",
                ).fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_exists_in_pages(self):
        response_index = PostPagesTests.authorized_client.get(
            reverse("posts:index"),
        )
        response_group = PostPagesTests.authorized_client.get(
            reverse("posts:group_list", args=[PostPagesTests.group.slug])
        )
        response_profile = PostPagesTests.authorized_client.get(
            reverse("posts:profile", args=[PostPagesTests.user.username])
        )
        responses = [response_index, response_group, response_profile]
        for response in responses:
            with self.subTest(response=response):
                self.assertIn(
                    PostPagesTests.post,
                    response.context["page_obj"],
                )

    def test_post_not_exists_on_another_group_page(self):
        response = PostPagesTests.authorized_client.get(
            reverse(
                "posts:group_list",
                args=[PostPagesTests.group_another.slug],
            )
        )
        self.assertNotIn(
            PostPagesTests.group_another,
            response.context["page_obj"],
        )



class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="TestName")

        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        for i in range(13):
            Post.objects.create(
                text="Тестовый текст",
                author=cls.user,
                group=cls.group,
            )

    def tearDown(self):
        cache.clear()

    def test_paginator_first_page_contains_ten_records(self):
        reverse_names = [
            reverse("posts:index"),
            reverse(
                "posts:group_list",
                args=[PaginatorViewsTest.group.slug],
            ),
            reverse(
                "posts:profile",
                args=[PaginatorViewsTest.user.username],
            ),
        ]

        for name in reverse_names:
            with self.subTest(name=name):
                self.assertEqual(
                    len(
                        self.client.get(
                            name,
                        ).context["page_obj"],
                    ),
                    10,
                )

    def test_paginator_second_page_contains_three_records(self):
        reverse_names = [
            reverse("posts:index") + "/?page=2",
            reverse(
                "posts:group_list",
                args=[PaginatorViewsTest.group.slug],
            )
            + "?page=2",
            reverse(
                "posts:profile",
                args=[PaginatorViewsTest.user.username],
            )
            + "?page=2",
        ]

        for name in reverse_names:
            with self.subTest(name=name):
                self.assertEqual(
                    len(
                        self.client.get(
                            name,
                        ).context["page_obj"]
                    ),
                    (Post.objects.count() - 10),
                )
