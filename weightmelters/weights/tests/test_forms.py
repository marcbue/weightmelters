import datetime
from decimal import Decimal

import pytest

from weightmelters.users.tests.factories import UserFactory
from weightmelters.weights.forms import WeightEntryForm
from weightmelters.weights.tests.factories import WeightEntryFactory


@pytest.mark.django_db
class TestWeightEntryForm:
    def test_valid_form(self):
        """Test form with valid data."""
        form = WeightEntryForm(data={"date": "2024-01-15", "weight": "75.5"})
        assert form.is_valid()

    def test_empty_form_invalid(self):
        """Test form with empty data is invalid."""
        form = WeightEntryForm(data={})
        assert not form.is_valid()
        assert "date" in form.errors
        assert "weight" in form.errors

    def test_negative_weight_invalid(self):
        """Test form rejects negative weight."""
        form = WeightEntryForm(data={"date": "2024-01-15", "weight": "-5"})
        assert not form.is_valid()
        assert "weight" in form.errors

    def test_zero_weight_invalid(self):
        """Test form rejects zero weight."""
        form = WeightEntryForm(data={"date": "2024-01-15", "weight": "0"})
        assert not form.is_valid()
        assert "weight" in form.errors

    def test_excessive_weight_invalid(self):
        """Test form rejects weight over max limit."""
        form = WeightEntryForm(data={"date": "2024-01-15", "weight": "1000"})
        assert not form.is_valid()
        assert "weight" in form.errors

    def test_valid_weight_range(self):
        """Test form accepts weights in valid range."""
        for weight in ["30", "75.5", "150.25", "500"]:
            form = WeightEntryForm(data={"date": "2024-01-15", "weight": weight})
            assert form.is_valid(), f"Weight {weight} should be valid"

    def test_form_initial_with_existing_entry(self):
        """Test form pre-fills with existing entry data."""
        user = UserFactory()
        entry = WeightEntryFactory(
            user=user,
            date=datetime.date(2024, 1, 15),
            weight=Decimal("80.00"),
        )
        form = WeightEntryForm(instance=entry)
        assert form.initial["date"] == datetime.date(2024, 1, 15)
        assert form.initial["weight"] == Decimal("80.00")

    def test_date_defaults_to_today(self):
        """Test date field defaults to today when no initial provided."""
        form = WeightEntryForm()
        # initial is a callable, so we call it to get the actual value
        initial = form.fields["date"].initial
        if callable(initial):
            initial = initial()
        assert initial == datetime.date.today()
