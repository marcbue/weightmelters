import datetime
from decimal import Decimal

import pytest
from django.test import Client
from django.urls import reverse

from weightmelters.users.tests.factories import UserFactory
from weightmelters.weights.models import WeightEntry
from weightmelters.weights.tests.factories import WeightEntryFactory


@pytest.mark.django_db
class TestWeightLogView:
    def test_log_weight_requires_login(self, client: Client):
        """Test that log weight view requires authentication."""
        url = reverse("weights:log")
        response = client.post(url, {"date": "2024-01-15", "weight": "75.5"})
        assert response.status_code == 302
        assert "/accounts/login/" in response["Location"]

    def test_log_weight_creates_entry(self, client: Client):
        """Test logging a new weight entry."""
        user = UserFactory()
        client.force_login(user)

        url = reverse("weights:log")
        response = client.post(
            url,
            {"date": "2024-01-15", "weight": "75.5"},
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == 200
        entry = WeightEntry.objects.get(user=user, date=datetime.date(2024, 1, 15))
        assert entry.weight == Decimal("75.5")

    def test_log_weight_updates_existing_entry(self, client: Client):
        """Test updating an existing weight entry for same date."""
        user = UserFactory()
        entry = WeightEntryFactory(
            user=user,
            date=datetime.date(2024, 1, 15),
            weight=Decimal("70.0"),
        )
        client.force_login(user)

        url = reverse("weights:log")
        response = client.post(
            url,
            {"date": "2024-01-15", "weight": "75.5"},
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == 200
        entry.refresh_from_db()
        assert entry.weight == Decimal("75.5")
        assert WeightEntry.objects.filter(user=user, date=datetime.date(2024, 1, 15)).count() == 1

    def test_log_weight_invalid_data(self, client: Client):
        """Test logging with invalid data returns form with errors."""
        user = UserFactory()
        client.force_login(user)

        url = reverse("weights:log")
        response = client.post(
            url,
            {"date": "2024-01-15", "weight": "-5"},
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == 200
        assert WeightEntry.objects.filter(user=user).count() == 0

    def test_htmx_response_contains_graph(self, client: Client):
        """Test HTMX response triggers graph refresh."""
        user = UserFactory()
        client.force_login(user)

        url = reverse("weights:log")
        response = client.post(
            url,
            {"date": "2024-01-15", "weight": "75.5"},
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == 200
        assert "HX-Trigger" in response.headers


@pytest.mark.django_db
class TestWeightGraphView:
    def test_graph_requires_login(self, client: Client):
        """Test that graph view requires authentication."""
        url = reverse("weights:graph")
        response = client.get(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response["Location"]

    def test_graph_returns_html(self, client: Client):
        """Test graph view returns HTML partial."""
        user = UserFactory()
        client.force_login(user)

        url = reverse("weights:graph")
        response = client.get(url)

        assert response.status_code == 200
        assert "text/html" in response["Content-Type"]

    def test_graph_shows_all_users_data(self, client: Client):
        """Test graph includes data from all users."""
        user1 = UserFactory(username="user1")
        user2 = UserFactory(username="user2")
        WeightEntryFactory(user=user1, weight=Decimal("70.0"))
        WeightEntryFactory(user=user2, weight=Decimal("80.0"))

        client.force_login(user1)
        url = reverse("weights:graph")
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        # Both users should appear in the graph (in legend or data)
        assert "user1" in content
        assert "user2" in content


@pytest.mark.django_db
class TestWeightDeleteView:
    def test_delete_requires_login(self, client: Client):
        """Test delete view requires authentication."""
        entry = WeightEntryFactory()
        url = reverse("weights:delete", kwargs={"pk": entry.pk})
        response = client.delete(url)
        assert response.status_code == 302

    def test_delete_own_entry(self, client: Client):
        """Test user can delete their own entry."""
        user = UserFactory()
        entry = WeightEntryFactory(user=user)
        client.force_login(user)

        url = reverse("weights:delete", kwargs={"pk": entry.pk})
        response = client.delete(url, HTTP_HX_REQUEST="true")

        assert response.status_code == 200
        assert not WeightEntry.objects.filter(pk=entry.pk).exists()

    def test_cannot_delete_other_user_entry(self, client: Client):
        """Test user cannot delete another user's entry."""
        user = UserFactory()
        other_user = UserFactory()
        entry = WeightEntryFactory(user=other_user)
        client.force_login(user)

        url = reverse("weights:delete", kwargs={"pk": entry.pk})
        response = client.delete(url, HTTP_HX_REQUEST="true")

        assert response.status_code == 404
        assert WeightEntry.objects.filter(pk=entry.pk).exists()

    def test_delete_triggers_graph_refresh(self, client: Client):
        """Test delete returns HX-Trigger for graph refresh."""
        user = UserFactory()
        entry = WeightEntryFactory(user=user)
        client.force_login(user)

        url = reverse("weights:delete", kwargs={"pk": entry.pk})
        response = client.delete(url, HTTP_HX_REQUEST="true")

        assert "HX-Trigger" in response.headers


@pytest.mark.django_db
class TestHomeView:
    def test_home_shows_form_when_authenticated(self, client: Client):
        """Test home page shows weight form for logged in users."""
        user = UserFactory()
        client.force_login(user)

        url = reverse("home")
        response = client.get(url)

        assert response.status_code == 200

    def test_home_prefills_todays_weight(self, client: Client):
        """Test home page prefills form with today's weight if exists."""
        user = UserFactory()
        today = datetime.date.today()
        WeightEntryFactory(user=user, date=today, weight=Decimal("75.5"))
        client.force_login(user)

        url = reverse("home")
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "75.5" in content or "75.50" in content
