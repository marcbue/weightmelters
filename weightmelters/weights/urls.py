from django.urls import path

from weightmelters.weights.views import delete_weight
from weightmelters.weights.views import log_weight
from weightmelters.weights.views import weight_entries
from weightmelters.weights.views import weight_graph

app_name = "weights"

urlpatterns = [
    path("log/", log_weight, name="log"),
    path("graph/", weight_graph, name="graph"),
    path("entries/", weight_entries, name="entries"),
    path("<int:pk>/delete/", delete_weight, name="delete"),
]
