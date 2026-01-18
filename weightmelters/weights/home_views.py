from typing import Any

from django.http import HttpRequest
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from weightmelters.weights.forms import WeightEntryForm
from weightmelters.weights.models import WeightEntry


def home(request: HttpRequest) -> HttpResponse:
    """Home page view with weight form and graph for authenticated users."""
    context: dict[str, Any] = {}

    if request.user.is_authenticated:
        today = timezone.localdate()
        existing_entry = WeightEntry.objects.filter(
            user=request.user,
            date=today,
        ).first()

        if existing_entry:
            form = WeightEntryForm(instance=existing_entry)
        else:
            form = WeightEntryForm()

        context["form"] = form
        context["existing_entry"] = existing_entry

    return render(request, "pages/home.html", context)
