from django.urls import path
from ledger.api_views import TransferView, FreezeView, UnfreezeView

urlpatterns = [
    path("transfer/", TransferView.as_view(), name="transfer"),
    path("freeze/", FreezeView.as_view(), name="freeze"),
    path("unfreeze/", UnfreezeView.as_view(), name="unfreeze"),
]