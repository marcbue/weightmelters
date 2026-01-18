from allauth.account.forms import SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from django import forms
from django.contrib.auth import forms as admin_forms
from django.forms import EmailField
from django.utils.translation import gettext_lazy as _

from .models import User

MAX_AVATAR_SIZE = 1024 * 1024  # 1MB


class CroppedAvatarForm(forms.Form):
    """Form for uploading a cropped avatar image."""

    avatar = forms.ImageField(
        label=_("Avatar"),
        help_text=_("Upload an image (max 1MB)."),
    )

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if avatar:
            if avatar.size > MAX_AVATAR_SIZE:
                msg = _("Avatar file is too large. Maximum size is 1MB.")
                raise forms.ValidationError(msg)
        return avatar


class UserAdminChangeForm(admin_forms.UserChangeForm):
    class Meta(admin_forms.UserChangeForm.Meta):  # type: ignore[name-defined]
        model = User
        field_classes = {"email": EmailField}


class UserAdminCreationForm(admin_forms.AdminUserCreationForm):
    """
    Form for User Creation in the Admin Area.
    To change user signup, see UserSignupForm and UserSocialSignupForms.
    """

    class Meta(admin_forms.UserCreationForm.Meta):  # type: ignore[name-defined]
        model = User
        fields = ("email",)
        field_classes = {"email": EmailField}
        error_messages = {
            "email": {"unique": _("This email has already been taken.")},
        }


class UserSignupForm(SignupForm):
    """
    Form that will be rendered on a user sign up section/screen.
    Default fields will be added automatically.
    Check UserSocialSignupForm for accounts created from social.
    """


class UserSocialSignupForm(SocialSignupForm):
    """
    Renders the form when user has signed up using social accounts.
    Default fields will be added automatically.
    See UserSignupForm otherwise.
    """
