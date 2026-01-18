import json

from avatar.models import Avatar
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import DetailView
from django.views.generic import RedirectView
from django.views.generic import UpdateView

from weightmelters.users.forms import CroppedAvatarForm
from weightmelters.users.models import User


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    fields = ["name"]
    success_message = _("Information successfully updated")

    def get_success_url(self) -> str:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user.get_absolute_url()

    def get_object(self, queryset: QuerySet | None = None) -> User:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self) -> str:
        return reverse("users:detail", kwargs={"pk": self.request.user.pk})


user_redirect_view = UserRedirectView.as_view()


class AvatarUploadView(LoginRequiredMixin, View):
    """View for uploading a cropped avatar image."""

    def get(self, request: HttpRequest) -> HttpResponse:
        """Return the avatar crop modal HTML."""
        form = CroppedAvatarForm()
        return render(
            request,
            "users/partials/avatar_crop_modal.html",
            {"form": form},
        )

    def post(self, request: HttpRequest) -> HttpResponse:
        """Save the cropped avatar image."""
        form = CroppedAvatarForm(request.POST, request.FILES)
        if form.is_valid():
            avatar_file = form.cleaned_data["avatar"]

            # Delete existing avatars for this user
            Avatar.objects.filter(user=request.user).delete()

            # Create new avatar
            Avatar.objects.create(
                user=request.user,
                avatar=avatar_file,
                primary=True,
            )

            response = render(
                request,
                "users/partials/avatar_upload_success.html",
            )
            response["HX-Trigger"] = json.dumps({"avatarUpdated": True})
            return response

        # Return form with errors
        return render(
            request,
            "users/partials/avatar_crop_modal.html",
            {"form": form},
        )


avatar_upload_view = AvatarUploadView.as_view()
