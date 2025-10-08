from django.urls import path
from . import views
from authapp.api import RegisterWithInviteView, ProfileView

urlpatterns = [
    path('', views.auth_view, name='auth'),
    path('auth/', views.auth_view, name='auth'),
    path('logout/', views.logout_view, name='logout'),
    path("register/", RegisterWithInviteView.as_view(), name="register_with_invite"),
    path("profile/", ProfileView.as_view(), name="profile"),
]
