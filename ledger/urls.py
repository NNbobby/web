from django.urls import path
from ledger.api_views import TransferView, FreezeView, UnfreezeView
from authapp.api import RegisterWithInviteView, ProfileView

urlpatterns = [
    path("transfer/", TransferView.as_view(), name="transfer"),
    path("freeze/", FreezeView.as_view(), name="freeze"),
    path("unfreeze/", UnfreezeView.as_view(), name="unfreeze"),
    path("register/", RegisterWithInviteView.as_view(), name="register_with_invite"),
    path("profile/", ProfileView.as_view(), name="profile"),
]