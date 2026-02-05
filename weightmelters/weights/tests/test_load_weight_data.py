import json
from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command

from weightmelters.users.models import User
from weightmelters.weights.models import WeightEntry

TEST_PASSWORD = "test123"  # noqa: S105


@pytest.fixture
def users(db):
    """Create test users."""
    return {
        "Alice": User.objects.create_user(
            email="alice@example.com",
            password=TEST_PASSWORD,
            name="Alice",
        ),
        "Bob": User.objects.create_user(
            email="bob@example.com",
            password=TEST_PASSWORD,
            name="Bob",
        ),
    }


@pytest.fixture
def valid_json_file(tmp_path):
    """Create a valid JSON file with weight data."""
    data = {
        "users": ["Alice", "Bob"],
        "entries": [
            {"date": "2026-01-01", "weights": {"Alice": "70.5", "Bob": "80.0"}},
            {"date": "2026-01-02", "weights": {"Alice": "70.3"}},
        ],
    }
    file_path = tmp_path / "weight_data.json"
    file_path.write_text(json.dumps(data))
    return file_path


class TestLoadWeightDataCommand:
    def test_file_not_found(self, db):
        """Command should fail gracefully when file doesn't exist."""
        out = StringIO()
        err = StringIO()

        call_command(
            "load_weight_data",
            file="/nonexistent/path.json",
            stdout=out,
            stderr=err,
        )

        assert "not found" in err.getvalue().lower()

    def test_invalid_json(self, tmp_path, db):
        """Command should fail gracefully on invalid JSON."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ invalid json }")

        out = StringIO()
        err = StringIO()

        call_command(
            "load_weight_data",
            file=str(invalid_file),
            stdout=out,
            stderr=err,
        )

        assert "invalid json" in err.getvalue().lower()

    def test_missing_users_key(self, tmp_path, db):
        """Command should fail when 'users' key is missing."""
        data = {"entries": []}
        file_path = tmp_path / "no_users.json"
        file_path.write_text(json.dumps(data))

        out = StringIO()
        err = StringIO()

        call_command(
            "load_weight_data",
            file=str(file_path),
            stdout=out,
            stderr=err,
        )

        assert "users" in err.getvalue().lower()

    def test_missing_entries_key(self, tmp_path, db):
        """Command should fail when 'entries' key is missing."""
        data = {"users": ["Alice"]}
        file_path = tmp_path / "no_entries.json"
        file_path.write_text(json.dumps(data))

        out = StringIO()
        err = StringIO()

        call_command(
            "load_weight_data",
            file=str(file_path),
            stdout=out,
            stderr=err,
        )

        assert "entries" in err.getvalue().lower()

    def test_user_not_found(self, valid_json_file, db):
        """Command should fail when a user in the JSON doesn't exist."""
        out = StringIO()
        err = StringIO()

        call_command(
            "load_weight_data",
            file=str(valid_json_file),
            stdout=out,
            stderr=err,
        )

        assert "not found" in err.getvalue().lower()

    def test_successful_data_loading(self, valid_json_file, users):
        """Command should successfully load weight entries."""
        out = StringIO()
        err = StringIO()

        call_command(
            "load_weight_data",
            file=str(valid_json_file),
            stdout=out,
            stderr=err,
        )

        # Check entries were created (3 total: 2 Alice + 1 Bob)
        expected_total = 3
        expected_alice = 2
        assert WeightEntry.objects.count() == expected_total
        alice_entries = WeightEntry.objects.filter(user=users["Alice"])
        assert alice_entries.count() == expected_alice
        bob_entries = WeightEntry.objects.filter(user=users["Bob"])
        assert bob_entries.count() == 1

        # Check values
        alice_jan1 = alice_entries.get(date="2026-01-01")
        assert alice_jan1.weight == Decimal("70.5")

        # Check output
        output = out.getvalue()
        assert "created" in output.lower()

    def test_dry_run_mode(self, valid_json_file, users):
        """Dry run should validate without saving."""
        out = StringIO()
        err = StringIO()

        call_command(
            "load_weight_data",
            file=str(valid_json_file),
            dry_run=True,
            stdout=out,
            stderr=err,
        )

        # No entries should be created
        assert WeightEntry.objects.count() == 0

        # Should indicate dry run
        output = out.getvalue()
        assert "dry run" in output.lower() or "would" in output.lower()

    def test_sparse_data_handling(self, tmp_path, users):
        """Command should handle sparse data (not all users each day)."""
        data = {
            "users": ["Alice", "Bob"],
            "entries": [
                {"date": "2026-01-01", "weights": {"Alice": "70.5"}},
                {"date": "2026-01-02", "weights": {"Bob": "80.0"}},
                {"date": "2026-01-03", "weights": {}},
            ],
        }
        file_path = tmp_path / "sparse.json"
        file_path.write_text(json.dumps(data))

        out = StringIO()
        err = StringIO()

        call_command(
            "load_weight_data",
            file=str(file_path),
            stdout=out,
            stderr=err,
        )

        # Only 2 entries (one per user, skipping empty day)
        expected_entries = 2
        assert WeightEntry.objects.count() == expected_entries

    def test_update_existing_entries(self, valid_json_file, users):
        """Command should update existing entries instead of duplicating."""
        # Create an existing entry
        WeightEntry.objects.create(
            user=users["Alice"],
            date="2026-01-01",
            weight=Decimal("99.9"),
        )

        out = StringIO()
        err = StringIO()

        call_command(
            "load_weight_data",
            file=str(valid_json_file),
            stdout=out,
            stderr=err,
        )

        # Should still have 3 total entries (1 updated + 2 created)
        expected_entries = 3
        assert WeightEntry.objects.count() == expected_entries

        # The existing entry should be updated
        alice_jan1 = WeightEntry.objects.get(user=users["Alice"], date="2026-01-01")
        assert alice_jan1.weight == Decimal("70.5")

        output = out.getvalue()
        assert "updated" in output.lower()

    def test_invalid_date_format(self, tmp_path, users):
        """Command should fail gracefully on invalid date format."""
        data = {
            "users": ["Alice"],
            "entries": [{"date": "01-01-2026", "weights": {"Alice": "70.5"}}],
        }
        file_path = tmp_path / "bad_date.json"
        file_path.write_text(json.dumps(data))

        out = StringIO()
        err = StringIO()

        call_command(
            "load_weight_data",
            file=str(file_path),
            stdout=out,
            stderr=err,
        )

        error_msg = err.getvalue().lower()
        assert "date" in error_msg or "invalid" in error_msg

    def test_invalid_weight_value(self, tmp_path, users):
        """Command should fail gracefully on invalid weight value."""
        data = {
            "users": ["Alice"],
            "entries": [{"date": "2026-01-01", "weights": {"Alice": "not-a-number"}}],
        }
        file_path = tmp_path / "bad_weight.json"
        file_path.write_text(json.dumps(data))

        out = StringIO()
        err = StringIO()

        call_command(
            "load_weight_data",
            file=str(file_path),
            stdout=out,
            stderr=err,
        )

        error_msg = err.getvalue().lower()
        assert "weight" in error_msg or "invalid" in error_msg

    def test_default_file_path(self, db, monkeypatch):
        """Command should use default path when no file specified."""
        out = StringIO()
        err = StringIO()

        # The default file won't exist, so it should error with file not found
        call_command(
            "load_weight_data",
            stdout=out,
            stderr=err,
        )

        # Should reference the default path in error
        error_output = err.getvalue()
        assert (
            "data/weight_data.json" in error_output
            or "not found" in error_output.lower()
        )
