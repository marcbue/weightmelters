import datetime
from decimal import Decimal

import pytest
from django.db import IntegrityError

from weightmelters.users.tests.factories import UserFactory
from weightmelters.weights.models import WeightEntry
from weightmelters.weights.tests.factories import WeightEntryFactory


@pytest.mark.django_db
class TestWeightEntryModel:
    def test_create_weight_entry(self):
        """Test creating a weight entry."""
        entry = WeightEntryFactory(weight=Decimal("75.50"))
        assert entry.pk is not None
        assert entry.weight == Decimal("75.50")
        assert entry.user is not None
        assert entry.date is not None

    def test_str_representation(self):
        """Test string representation of weight entry."""
        user = UserFactory(username="testuser")
        entry = WeightEntryFactory(
            user=user,
            date=datetime.date(2024, 1, 15),
            weight=Decimal("80.00"),
        )
        assert str(entry) == "testuser - 2024-01-15: 80.00 kg"

    def test_unique_together_user_date(self):
        """Test that user can only have one entry per date."""
        user = UserFactory()
        date = datetime.date(2024, 1, 15)
        WeightEntryFactory(user=user, date=date)

        with pytest.raises(IntegrityError):
            WeightEntryFactory(user=user, date=date)

    def test_same_date_different_users(self):
        """Test that different users can have entries on same date."""
        date = datetime.date(2024, 1, 15)
        entry1 = WeightEntryFactory(date=date)
        entry2 = WeightEntryFactory(date=date)

        assert entry1.date == entry2.date
        assert entry1.user != entry2.user

    def test_ordering_by_date_descending(self):
        """Test that entries are ordered by date descending."""
        user = UserFactory()
        entry1 = WeightEntryFactory(user=user, date=datetime.date(2024, 1, 10))
        entry2 = WeightEntryFactory(user=user, date=datetime.date(2024, 1, 15))
        entry3 = WeightEntryFactory(user=user, date=datetime.date(2024, 1, 12))

        entries = list(WeightEntry.objects.filter(user=user))
        assert entries[0] == entry2  # Most recent first
        assert entries[1] == entry3
        assert entries[2] == entry1

    def test_weight_decimal_precision(self):
        """Test that weight has correct decimal precision."""
        entry = WeightEntryFactory(weight=Decimal("123.45"))
        entry.refresh_from_db()
        assert entry.weight == Decimal("123.45")

    def test_timestamps_auto_set(self):
        """Test that created_at and updated_at are automatically set."""
        entry = WeightEntryFactory()
        assert entry.created_at is not None
        assert entry.updated_at is not None

    def test_updated_at_changes_on_update(self):
        """Test that updated_at changes when entry is modified."""
        entry = WeightEntryFactory()
        original_updated_at = entry.updated_at

        entry.weight = Decimal("99.99")
        entry.save()
        entry.refresh_from_db()

        assert entry.updated_at >= original_updated_at
