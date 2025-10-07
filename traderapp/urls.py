from django.urls import path
from . import views

urlpatterns = [
    path('purchases/', views.purchases, name='purchases'),  
    path('news/', views.news_view, name='news'),
    path('cancel_bid/<int:bid_id>/', views.cancel_bid, name='cancel_bid'),
    path('sales/', views.sales, name='sales'),  
    path('deposit/', views.deposit, name='deposit'),
    path('referrals/', views.referrals, name='referrals'),  
    path('statistics/', views.statistics, name='statistics'),  
    path('api/', views.api, name='api'),  
    path('settings/', views.settings, name='settings'),  
    path('faq/', views.faq, name='faq'),  
    path('wallets/', views.wallets, name='wallets'),  
    path('accept_bid/<int:bid_id>/', views.accept_bid, name='accept_bid'),
    path('api/update_rate/', views.fetch_and_sync_exchange_rate, name='fetch_exchange_rate'),
    path('wallets/api/', views.api_wallets, name='api_wallets'),
    path('wallets-add/', views.add_wallet, name='add_wallet'),
    path('wallets-update-status/<int:wallet_id>/', views.update_wallet_status, name='update_wallet_status'),
    path('wallets-get/<int:wallet_id>/', views.get_wallet, name='get_wallet'),  # Новый маршрут
    path('wallets-delete/<int:wallet_id>/', views.delete_wallet, name='delete_wallet'),
    path('api/deposit/', views.create_deposit_request, name='api_create_deposit_request'),
    path('api/deposit/<int:requestId>/cancel/', views.cancel_deposit_request, name='api_cancel_deposit_request'),
]
