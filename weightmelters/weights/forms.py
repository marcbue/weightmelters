import datetime
from decimal import Decimal

from django import forms
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator

from weightmelters.weights.models import WeightEntry


class WeightEntryForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        initial=datetime.date.today,
    )
    weight = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.01"), message="Weight must be greater than 0"),
            MaxValueValidator(Decimal("999.99"), message="Weight must be less than 1000 kg"),
        ],
        widget=forms.NumberInput(
            attrs={
                "type": "number",
                "step": "0.01",
                "min": "0.01",
                "max": "999.99",
                "class": "form-control",
                "placeholder": "Weight in kg",
            }
        ),
    )

    class Meta:
        model = WeightEntry
        fields = ["date", "weight"]
