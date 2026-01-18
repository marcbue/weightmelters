import datetime
import hashlib
import json

import plotly.graph_objects as go
from avatar.models import Avatar
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_http_methods

from weightmelters.weights.forms import WeightEntryForm
from weightmelters.weights.models import WeightEntry


def get_gravatar_url(email: str, size: int = 40) -> str:
    """Get Gravatar URL for an email address."""
    # MD5 is required by Gravatar's API spec
    email_hash = hashlib.md5(email.lower().encode()).hexdigest()  # noqa: S324
    return f"https://www.gravatar.com/avatar/{email_hash}?d=identicon&s={size}"


def get_user_avatar_url(user, size: int = 40) -> str:
    """Get avatar URL for user, falling back to Gravatar."""
    try:
        avatar = Avatar.objects.get(user=user, primary=True)
        # Check if the avatar file actually exists and can be opened
        if avatar.avatar:
            try:
                avatar.avatar.open()
                avatar.avatar.close()
                # Use original avatar URL - CSS handles sizing in the tooltip
                url = avatar.avatar.url
                if url and url.startswith(("http", "/")):
                    return url
            except Exception:  # noqa: BLE001, S110
                pass  # File missing, corrupted, or other issue - fall back to Gravatar
    except Avatar.DoesNotExist:
        pass
    return get_gravatar_url(user.email, size)


@login_required
@require_http_methods(["POST"])
def log_weight(request):
    """Log or update a weight entry."""
    date_str = request.POST.get("date")
    if date_str:
        try:
            date = (
                datetime.datetime.strptime(date_str, "%Y-%m-%d")
                .replace(
                    tzinfo=datetime.UTC,
                )
                .date()
            )
            existing_entry = WeightEntry.objects.filter(
                user=request.user,
                date=date,
            ).first()
        except ValueError:
            existing_entry = None
    else:
        existing_entry = None

    form = WeightEntryForm(request.POST, instance=existing_entry)

    if form.is_valid():
        entry = form.save(commit=False)
        entry.user = request.user
        entry.save()

        response = render(
            request,
            "weights/partials/weight_form.html",
            {"form": WeightEntryForm(instance=entry), "success": True},
        )
        response["HX-Trigger"] = json.dumps(
            {"refreshGraph": True, "refreshEntries": True},
        )
        return response

    return render(
        request,
        "weights/partials/weight_form.html",
        {"form": form},
    )


@login_required
@require_GET
def weight_graph(request):
    """Return the weight graph as HTML."""
    entries = WeightEntry.objects.select_related("user").order_by("date")

    # Group entries by user (keyed by user.pk to handle duplicate display names)
    user_data: dict[int, dict[str, list]] = {}
    user_info: dict[int, dict[str, str]] = {}

    for entry in entries:
        user_pk = entry.user.pk
        if user_pk not in user_data:
            display_name = entry.user.get_display_name()
            avatar_url = get_user_avatar_url(entry.user, size=40)
            user_data[user_pk] = {"dates": [], "weights": [], "customdata": []}
            user_info[user_pk] = {
                "display_name": display_name,
                "email": entry.user.email,
                "avatar_url": avatar_url,
            }
        user_data[user_pk]["dates"].append(entry.date)
        user_data[user_pk]["weights"].append(float(entry.weight))
        user_data[user_pk]["customdata"].append(
            {
                "email": entry.user.email,
                "avatar_url": user_info[user_pk]["avatar_url"],
                "display_name": user_info[user_pk]["display_name"],
            },
        )

    # Return empty state if no data
    if not user_data:
        return render(
            request,
            "weights/partials/graph.html",
            {"graph_html": None},
        )

    # Create Plotly figure
    fig = go.Figure()

    for user_pk, data in user_data.items():
        fig.add_trace(
            go.Scatter(
                x=data["dates"],
                y=data["weights"],
                mode="lines+markers",
                name=user_info[user_pk]["display_name"],
                customdata=data["customdata"],
                hoverinfo="none",
            ),
        )

    fig.update_layout(
        title="Weight Tracking",
        xaxis_title="Date",
        yaxis_title="Weight (kg)",
        hovermode="closest",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
        margin={"l": 40, "r": 40, "t": 60, "b": 40},
        height=400,
    )

    # Convert to HTML div (Plotly.js is loaded globally in home.html)
    graph_html = fig.to_html(full_html=False, include_plotlyjs=False)

    return render(
        request,
        "weights/partials/graph.html",
        {"graph_html": graph_html},
    )


@login_required
@require_http_methods(["DELETE"])
def delete_weight(request, pk):
    """Delete a weight entry."""
    entry = get_object_or_404(WeightEntry, pk=pk, user=request.user)
    entry.delete()

    response = HttpResponse(status=200)
    response["HX-Trigger"] = json.dumps({"refreshGraph": True, "refreshEntries": True})
    return response


def get_weight_form_context(user):
    """Get the context for the weight form, prefilled with today's entry if exists."""
    today = timezone.localdate()
    existing_entry = WeightEntry.objects.filter(user=user, date=today).first()

    if existing_entry:
        form = WeightEntryForm(instance=existing_entry)
    else:
        form = WeightEntryForm()

    return {"form": form, "existing_entry": existing_entry}


@login_required
@require_GET
def weight_entries(request):
    """Return the user's weight entries list."""
    entries = WeightEntry.objects.filter(user=request.user).order_by("-date")[:10]
    return render(
        request,
        "weights/partials/entries_list.html",
        {"entries": entries},
    )
