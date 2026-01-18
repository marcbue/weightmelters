import datetime
from decimal import Decimal

from factory import LazyAttribute
from factory import SubFactory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyDecimal

from weightmelters.users.tests.factories import UserFactory
from weightmelters.weights.models import WeightEntry


class WeightEntryFactory(DjangoModelFactory):
    user = SubFactory(UserFactory)
    date = LazyAttribute(lambda _: datetime.date.today())
    weight = FuzzyDecimal(50.0, 150.0, precision=2)

    class Meta:
        model = WeightEntry
