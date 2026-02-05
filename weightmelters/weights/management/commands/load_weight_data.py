from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand

from weightmelters.users.models import User
from weightmelters.weights.models import WeightEntry

# Weight data: (year, month, day, Moldir, Marc, Roman, Andy, Theresa, Patricia)
# Empty string means no entry for that user on that day
WEIGHT_DATA = [
    (2026, 1, 6, "67.6", "76.95", "", "", "", ""),
    (2026, 1, 7, "67.2", "76.65", "", "", "", ""),
    (2026, 1, 8, "67.5", "76.35", "", "", "", ""),
    (2026, 1, 9, "67.6", "76.4", "", "", "", ""),
    (2026, 1, 10, "66.8", "76.3", "", "", "", ""),
    (2026, 1, 11, "66.9", "76.3", "", "", "", ""),
    (2026, 1, 12, "66.7", "76.2", "", "", "", ""),
    (2026, 1, 13, "66.3", "75.4", "", "", "", ""),
    (2026, 1, 14, "66.1", "75.1", "80", "79.1", "65", "61.7"),
    (2026, 1, 15, "66", "74.65", "79.9", "78.9", "65.2", "61.55"),
    (2026, 1, 16, "65.9", "75.75", "80.2", "79.3", "65.5", "61.2"),
    (2026, 1, 17, "66", "75.35", "80.6", "", "65.6", "60.45"),
    (2026, 1, 18, "66.2", "76.6", "80.4", "", "65.6", "60.7"),
    (2026, 1, 19, "66.2", "75", "", "79.7", "65.2", "60.8"),
    (2026, 1, 20, "65.8", "74.2", "80.3", "79.6", "65.4", "60.9"),
    (2026, 1, 21, "65.9", "74.7", "79.8", "78.6", "65.2", "60.8"),
    (2026, 1, 22, "65.3", "", "79.5", "79", "65.1", ""),
    (2026, 1, 23, "", "", "79.5", "", "65.4", ""),
    (2026, 1, 24, "64.5", "", "80.3", "79", "65", ""),
    (2026, 1, 25, "", "", "80", "", "", ""),
    (2026, 1, 26, "65.6", "73.7", "80.2", "", "", ""),
    (2026, 1, 27, "65.1", "73.65", "80.6", "78.5", "66.1", ""),
    (2026, 1, 28, "65.6", "73.9", "79.5", "", "", "61.8"),
    (2026, 1, 29, "65.4", "73.9", "79.8", "79.6", "65.7", "61.85"),
    (2026, 1, 30, "65", "73.5", "79.2", "", "", "60.9"),
    (2026, 1, 31, "65.8", "73.95", "80.5", "", "65.4", "61.05"),
    (2026, 2, 1, "", "", "80.9", "", "65.2", ""),
    (2026, 2, 2, "65.5", "", "80.2", "79.1", "64.7", "62.15"),
    (2026, 2, 3, "65.5", "74.6", "80", "78.2", "65.1", "61.05"),
    (2026, 2, 4, "65.1", "73.9", "79.5", "78.1", "", "60.6"),
    (2026, 2, 5, "64.5", "72.8", "79.5", "", "", "61.05"),
]

USER_NAMES = ["Moldir", "Marc", "Roman", "Andy", "Theresa", "Patricia"]


class Command(BaseCommand):
    help = "Load historical weight data for existing users"

    def handle(self, *args, **options):
        # Look up users by name
        users = {}
        for name in USER_NAMES:
            try:
                users[name] = User.objects.get(name__iexact=name)
                self.stdout.write(f"Found user: {name}")
            except User.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"User not found: {name}"))
                return
            except User.MultipleObjectsReturned:
                self.stderr.write(self.style.ERROR(f"Multiple users found: {name}"))
                return

        # Insert weight entries
        created_count = 0
        updated_count = 0

        for row in WEIGHT_DATA:
            year, month, day = row[0], row[1], row[2]
            entry_date = date(year, month, day)

            for i, name in enumerate(USER_NAMES):
                weight_str = row[i + 3]
                if not weight_str:
                    continue

                weight = Decimal(weight_str)
                user = users[name]

                _, created = WeightEntry.objects.update_or_create(
                    user=user,
                    date=entry_date,
                    defaults={"weight": weight},
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done! Created: {created_count}, Updated: {updated_count}"
            )
        )
