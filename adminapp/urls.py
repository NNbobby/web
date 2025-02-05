from django.urls import path
from . import views

urlpatterns = [
    path('add_user/', views.add_user, name='add_user'),
    path('news-adm/', views.newsadm, name='newsadm'),
    path('stats-adm/', views.statisticsadm, name='statisticsadm'),
    path('settings-adm/', views.settingsadm, name='settingsadm'),
    path('adm-db/', views.databaseadm, name='databaseadm'),
    path('add_bid/', views.add_bid, name='add_bid'),
    path('delete_bid/<int:bid_id>/', views.delete_bid, name='delete_bid'),
]
