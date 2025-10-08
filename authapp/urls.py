from django.urls import path
from . import views
from .api import RegisterView, ProfileView

urlpatterns = [
    path('', views.auth_view, name='auth'),
    path('auth/', views.auth_view, name='auth'),
    path('logout/', views.logout_view, name='logout'),
    path("register/", RegisterView.as_view(), name="register"),
    path("profile/", ProfileView.as_view(), name="profile"),
]
