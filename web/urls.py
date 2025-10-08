# web/urls.py
from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('authapp.urls')),  # Подключение всех маршрутов приложения authapp
    path('trade/', include('traderapp.urls')),  # Подключение всех маршрутов приложения traderapp
    path('payments/', include('paymentapp.urls')), #
    path('admin-panel/', include('adminapp.urls')), 
    path('private-lk/', include('clientapp.urls')), 
    path("api/ledger/", include("ledger.urls")),
    path('api/auth/', include('authapp.urls')),

    # JWT endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
