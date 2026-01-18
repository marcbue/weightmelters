import pytest
from django.test import Client

from weightmelters.users.models import User
from weightmelters.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def _media_storage(settings, tmpdir) -> None:
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user(db) -> User:
    return UserFactory()


@pytest.fixture
def admin_user(db) -> User:
    """Create an admin user with email-based authentication."""
    return User.objects.create_superuser(
        email="admin@example.com",
        password="password",  # noqa: S106
    )


@pytest.fixture
def admin_client(admin_user) -> Client:
    """A Django test client logged in as an admin user."""
    client = Client()
    client.force_login(admin_user)
    return client
