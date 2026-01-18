from weightmelters.users.models import User


def test_user_get_absolute_url(user: User):
    assert user.get_absolute_url() == f"/users/{user.pk}/"


def test_user_get_display_name_with_name(user: User):
    user.name = "Test User"
    assert user.get_display_name() == "Test User"


def test_user_get_display_name_without_name(user: User):
    user.name = ""
    # Should return email prefix
    assert user.get_display_name() == user.email.split("@")[0]
