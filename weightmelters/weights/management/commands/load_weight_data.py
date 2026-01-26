from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand

from weightmelters.users.models import User
from weightmelters.weights.models import WeightEntry

# Weight data: (day, Moldir, Marc, Roman, Andy, Theresa, Patricia)
# Empty string means no entry for that user on that day
WEIGHT_DATA = [
    (6, "67.6", "76.95", "", "", "", ""),
    (7, "67.2", "76.65", "", "", "", ""),
    (8, "67.5", "76.35", "", "", "", ""),
    (9, "67.6", "76.4", "", "", "", ""),
    (10, "66.8", "76.3", "", "", "", ""),
    (11, "66.9", "76.3", "", "", "", ""),
    (12, "66.7", "76.2", "", "", "", ""),
    (13, "66.3", "75.4", "", "", "", ""),
    (14, "66.1", "75.1", "80", "79.1", "65", "61.7"),
    (15, "66", "74.65", "79.9", "78.9", "65.2", "61.55"),
    (16, "65.9", "75.75", "80.2", "79.3", "65.5", "61.2"),
    (17, "66", "75.35", "80.6", "", "65.6", "60.45"),
    (18, "66.2", "76.6", "80.4", "", "65.6", "60.7"),
    (19, "66.2", "75", "", "79.7", "65.2", "60.8"),
    (20, "65.8", "74.2", "80.3", "79.6", "65.4", "60.9"),
    (21, "65.9", "74.7", "79.8", "78.6", "65.2", "60.8"),
    (22, "65.3", "", "79.5", "79", "65.1", ""),
    (23, "", "", "79.5", "", "65.4", ""),
    (24, "64.5", "", "80.3", "79", "65", ""),
    (25, "", "", "80", "", "", ""),
    (26, "65.6", "73.7", "80.2", "", "", ""),
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
            day = row[0]
            entry_date = date(2026, 1, day)

            for i, name in enumerate(USER_NAMES):
                weight_str = row[i + 1]
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
