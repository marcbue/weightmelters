from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from decimal import InvalidOperation
from pathlib import Path
from typing import TYPE_CHECKING

from django.core.management.base import BaseCommand

from weightmelters.users.models import User
from weightmelters.weights.models import WeightEntry

if TYPE_CHECKING:
    from argparse import ArgumentParser


DEFAULT_FILE = "data/weight_data.json"


class Command(BaseCommand):
    help = "Load weight data from a JSON file for existing users"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--file",
            type=str,
            default=DEFAULT_FILE,
            help=f"Path to JSON file (default: {DEFAULT_FILE})",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate data without saving to database",
        )

    def handle(self, *args, **options) -> None:
        file_path = Path(options["file"])
        dry_run = options["dry_run"]

        data = self._load_json_file(file_path)
        if data is None:
            return

        if not self._validate_structure(data):
            return

        user_names = data["users"]
        entries = data["entries"]

        users = self._lookup_users(user_names)
        if users is None:
            return

        entries_to_create = self._process_entries(entries, users, user_names)
        if entries_to_create is None:
            return

        if dry_run:
            self._print_dry_run(entries_to_create)
            return

        self._save_entries(entries_to_create)

    def _load_json_file(self, file_path: Path) -> dict | None:
        """Load and parse JSON file, returning None on error."""
        if not file_path.exists():
            self.stderr.write(self.style.ERROR(f"File not found: {file_path}"))
            return None

        try:
            with file_path.open() as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            self.stderr.write(self.style.ERROR(f"Invalid JSON in {file_path}: {e}"))
            return None

    def _validate_structure(self, data: dict) -> bool:
        """Validate JSON has required keys."""
        if "users" not in data:
            self.stderr.write(self.style.ERROR("Missing required key: 'users'"))
            return False

        if "entries" not in data:
            self.stderr.write(self.style.ERROR("Missing required key: 'entries'"))
            return False

        return True

    def _lookup_users(self, user_names: list[str]) -> dict[str, User] | None:
        """Look up users by name, returning None on error."""
        users = {}
        for name in user_names:
            try:
                users[name] = User.objects.get(name__iexact=name)
                self.stdout.write(f"Found user: {name}")
            except User.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"User not found: {name}"))
                return None
            except User.MultipleObjectsReturned:
                self.stderr.write(
                    self.style.ERROR(f"Multiple users found with name: {name}"),
                )
                return None
        return users

    def _process_entries(
        self,
        entries: list[dict],
        users: dict[str, User],
        user_names: list[str],
    ) -> list[dict] | None:
        """Process JSON entries into weight data, returning None on error."""
        entries_to_create = []

        for entry in entries:
            date_str = entry.get("date")
            if not date_str:
                self.stderr.write(self.style.ERROR("Entry missing 'date' field"))
                return None

            try:
                entry_date = datetime.strptime(date_str, "%Y-%m-%d").date()  # noqa: DTZ007
            except ValueError:
                self.stderr.write(
                    self.style.ERROR(
                        f"Invalid date format: {date_str} (expected YYYY-MM-DD)",
                    ),
                )
                return None

            weights = entry.get("weights", {})
            result = self._process_weights(
                weights,
                entry_date,
                users,
                user_names,
                date_str,
            )
            if result is None:
                return None
            entries_to_create.extend(result)

        return entries_to_create

    def _process_weights(
        self,
        weights: dict[str, str],
        entry_date,
        users: dict[str, User],
        user_names: list[str],
        date_str: str,
    ) -> list[dict] | None:
        """Process weights for a single date, returning None on error."""
        result = []
        for user_name, weight_str in weights.items():
            if user_name not in users:
                self.stderr.write(
                    self.style.ERROR(
                        f"Unknown user in weights: {user_name} "
                        f"(not in users list: {user_names})",
                    ),
                )
                return None

            if not weight_str:
                continue

            try:
                weight = Decimal(weight_str)
            except InvalidOperation:
                self.stderr.write(
                    self.style.ERROR(
                        f"Invalid weight value for {user_name} on {date_str}: "
                        f"'{weight_str}'",
                    ),
                )
                return None

            result.append(
                {
                    "user": users[user_name],
                    "date": entry_date,
                    "weight": weight,
                },
            )
        return result

    def _print_dry_run(self, entries_to_create: list[dict]) -> None:
        """Print dry run summary."""
        self.stdout.write(
            self.style.SUCCESS(
                f"Dry run: Would process {len(entries_to_create)} weight entries",
            ),
        )
        for entry_data in entries_to_create:
            self.stdout.write(
                f"  {entry_data['user'].name} on {entry_data['date']}: "
                f"{entry_data['weight']} kg",
            )

    def _save_entries(self, entries_to_create: list[dict]) -> None:
        """Save entries to database."""
        created_count = 0
        updated_count = 0

        for entry_data in entries_to_create:
            _, created = WeightEntry.objects.update_or_create(
                user=entry_data["user"],
                date=entry_data["date"],
                defaults={"weight": entry_data["weight"]},
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done! Created: {created_count}, Updated: {updated_count}",
            ),
        )
