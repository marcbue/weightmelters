from django.contrib import admin

from weightmelters.weights.models import WeightEntry


@admin.register(WeightEntry)
class WeightEntryAdmin(admin.ModelAdmin):
    list_display = ["user", "date", "weight", "created_at"]
    list_filter = ["date", "user"]
    search_fields = ["user__username"]
    date_hierarchy = "date"
    ordering = ["-date"]
