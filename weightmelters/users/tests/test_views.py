import random
from http import HTTPStatus
from io import BytesIO

import pytest
from avatar.models import Avatar
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpRequest
from django.http import HttpResponseRedirect
from django.test import RequestFactory
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from PIL import Image

from weightmelters.users.forms import UserAdminChangeForm
from weightmelters.users.models import User
from weightmelters.users.tests.factories import UserFactory
from weightmelters.users.views import UserRedirectView
from weightmelters.users.views import UserUpdateView
from weightmelters.users.views import user_detail_view

pytestmark = pytest.mark.django_db


class TestUserUpdateView:
    """
    TODO:
        extracting view initialization code as class-scoped fixture
        would be great if only pytest-django supported non-function-scoped
        fixture db access -- this is a work-in-progress for now:
        https://github.com/pytest-dev/pytest-django/pull/258
    """

    def dummy_get_response(self, request: HttpRequest):
        return None

    def test_get_success_url(self, user: User, rf: RequestFactory):
        view = UserUpdateView()
        request = rf.get("/fake-url/")
        request.user = user

        view.request = request
        assert view.get_success_url() == f"/users/{user.pk}/"

    def test_get_object(self, user: User, rf: RequestFactory):
        view = UserUpdateView()
        request = rf.get("/fake-url/")
        request.user = user

        view.request = request

        assert view.get_object() == user

    def test_form_valid(self, user: User, rf: RequestFactory):
        view = UserUpdateView()
        request = rf.get("/fake-url/")

        # Add the session/message middleware to the request
        SessionMiddleware(self.dummy_get_response).process_request(request)
        MessageMiddleware(self.dummy_get_response).process_request(request)
        request.user = user

        view.request = request

        # Initialize the form
        form = UserAdminChangeForm()
        form.cleaned_data = {}
        form.instance = user
        view.form_valid(form)

        messages_sent = [m.message for m in messages.get_messages(request)]
        assert messages_sent == [_("Information successfully updated")]


class TestUserRedirectView:
    def test_get_redirect_url(self, user: User, rf: RequestFactory):
        view = UserRedirectView()
        request = rf.get("/fake-url")
        request.user = user

        view.request = request
        assert view.get_redirect_url() == f"/users/{user.pk}/"


class TestUserDetailView:
    def test_authenticated(self, user: User, rf: RequestFactory):
        request = rf.get("/fake-url/")
        request.user = UserFactory()
        response = user_detail_view(request, pk=user.pk)

        assert response.status_code == HTTPStatus.OK

    def test_not_authenticated(self, user: User, rf: RequestFactory):
        request = rf.get("/fake-url/")
        request.user = AnonymousUser()
        response = user_detail_view(request, pk=user.pk)
        login_url = reverse(settings.LOGIN_URL)

        assert isinstance(response, HttpResponseRedirect)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == f"{login_url}?next=/fake-url/"

    def test_avatar_displayed_on_profile(self, user: User, client):
        """Test that avatar is displayed on user profile page."""
        client.force_login(user)
        response = client.get(reverse("users:detail", kwargs={"pk": user.pk}))

        assert response.status_code == HTTPStatus.OK
        content = response.content.decode()
        # Check avatar img tag is present (uses gravatar fallback)
        assert "<img" in content
        assert "gravatar.com" in content or "avatar" in content.lower()

    def test_change_avatar_button_for_own_profile(self, user: User, client):
        """Test that 'Change Avatar' button appears on own profile."""
        client.force_login(user)
        response = client.get(reverse("users:detail", kwargs={"pk": user.pk}))

        assert response.status_code == HTTPStatus.OK
        content = response.content.decode()
        # Button should trigger the crop modal
        assert 'data-bs-target="#avatarCropModal"' in content
        assert reverse("users:avatar-upload") in content

    def test_change_avatar_button_not_on_other_profile(self, user: User, client):
        """Test that 'Change Avatar' button does not appear on other user's profile."""
        other_user = UserFactory()
        client.force_login(user)
        response = client.get(reverse("users:detail", kwargs={"pk": other_user.pk}))

        assert response.status_code == HTTPStatus.OK
        content = response.content.decode()
        # Modal trigger button should not appear on other's profile
        assert 'data-bs-target="#avatarCropModal"' not in content


class TestAvatarUploadView:
    """Tests for the avatar upload view with cropping functionality."""

    def test_avatar_upload_requires_authentication(self, client):
        """Test that anonymous users cannot access avatar upload."""
        response = client.get(reverse("users:avatar-upload"))
        login_url = reverse(settings.LOGIN_URL)

        assert response.status_code == HTTPStatus.FOUND
        assert login_url in response.url

    def test_avatar_upload_get_returns_modal(self, user: User, client):
        """Test that GET request returns the crop modal HTML."""
        client.force_login(user)
        response = client.get(reverse("users:avatar-upload"))

        assert response.status_code == HTTPStatus.OK
        content = response.content.decode()
        assert "cropper" in content.lower() or "crop" in content.lower()

    def test_avatar_upload_post_with_valid_image(self, user: User, client, tmp_path):
        """Test that posting a valid image creates an avatar."""
        # Create a test image
        img = Image.new("RGB", (200, 200), color="red")
        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        uploaded_file = SimpleUploadedFile(
            "test.png",
            img_bytes.read(),
            content_type="image/png",
        )

        client.force_login(user)
        response = client.post(
            reverse("users:avatar-upload"),
            {"avatar": uploaded_file},
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == HTTPStatus.OK
        # Verify avatar was created
        assert Avatar.objects.filter(user=user).exists()

    def test_avatar_upload_replaces_existing_avatar(self, user: User, client):
        """Test that uploading replaces an existing avatar."""
        # Create initial avatar
        img1 = Image.new("RGB", (100, 100), color="blue")
        img1_bytes = BytesIO()
        img1.save(img1_bytes, format="PNG")
        img1_bytes.seek(0)
        uploaded_file1 = SimpleUploadedFile(
            "test1.png",
            img1_bytes.read(),
            content_type="image/png",
        )

        client.force_login(user)
        client.post(
            reverse("users:avatar-upload"),
            {"avatar": uploaded_file1},
            HTTP_HX_REQUEST="true",
        )
        initial_count = Avatar.objects.filter(user=user).count()

        # Upload new avatar
        img2 = Image.new("RGB", (100, 100), color="green")
        img2_bytes = BytesIO()
        img2.save(img2_bytes, format="PNG")
        img2_bytes.seek(0)
        uploaded_file2 = SimpleUploadedFile(
            "test2.png",
            img2_bytes.read(),
            content_type="image/png",
        )

        client.post(
            reverse("users:avatar-upload"),
            {"avatar": uploaded_file2},
            HTTP_HX_REQUEST="true",
        )

        # Should still have same number of avatars (replaced, not added)
        assert Avatar.objects.filter(user=user).count() == initial_count

    def test_avatar_upload_rejects_oversized_file(self, user: User, client, settings):
        """Test that files over 1MB are rejected."""
        # Create an oversized noisy image (> 1MB) that won't compress well
        random.seed(42)  # Reproducible randomness
        img = Image.new("RGB", (1000, 1000))
        for x in range(1000):
            for y in range(1000):
                img.putpixel(
                    (x, y),
                    (
                        random.randint(0, 255),  # noqa: S311
                        random.randint(0, 255),  # noqa: S311
                        random.randint(0, 255),  # noqa: S311
                    ),
                )
        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        uploaded_file = SimpleUploadedFile(
            "large.png",
            img_bytes.read(),
            content_type="image/png",
        )

        client.force_login(user)
        response = client.post(
            reverse("users:avatar-upload"),
            {"avatar": uploaded_file},
            HTTP_HX_REQUEST="true",
        )

        # Should return error (either 400 or 200 with error message)
        content = response.content.decode()
        # Check for error indication
        assert response.status_code in [HTTPStatus.OK, HTTPStatus.BAD_REQUEST]
        if response.status_code == HTTPStatus.OK:
            assert "error" in content.lower() or "too large" in content.lower()

    def test_avatar_upload_htmx_returns_trigger(self, user: User, client):
        """Test that successful upload returns HX-Trigger header."""
        img = Image.new("RGB", (100, 100), color="red")
        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        uploaded_file = SimpleUploadedFile(
            "test.png",
            img_bytes.read(),
            content_type="image/png",
        )

        client.force_login(user)
        response = client.post(
            reverse("users:avatar-upload"),
            {"avatar": uploaded_file},
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == HTTPStatus.OK
        assert "HX-Trigger" in response.headers
        assert "avatarUpdated" in response.headers["HX-Trigger"]
