from django.conf import settings
from django.db import models


class WeightEntry(models.Model):
    """A weight entry for a user on a specific date."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="weight_entries",
    )
    date = models.DateField()
    weight = models.DecimalField(max_digits=5, decimal_places=2)  # kg
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["user", "date"]
        ordering = ["-date"]
        verbose_name = "Weight Entry"
        verbose_name_plural = "Weight Entries"

    def __str__(self):
        return f"{self.user.username} - {self.date}: {self.weight} kg"
