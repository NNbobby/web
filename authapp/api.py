from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User

class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        tele_id = request.data.get("tele_id")
        username = request.data.get("username")
        role = request.data.get("role", "trader")

        user, created = User.objects.get_or_create(tele_id=tele_id, defaults={"username": username, "role": role})
        refresh = RefreshToken.for_user(user)
        return Response({
            "user_id": user.id,
            "role": user.role,
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        })


class ProfileView(generics.RetrieveAPIView):
    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "tele_id": user.tele_id,
            "role": user.role,
            "balance": str(user.balance),
            "escrow": str(user.escrow),
        })
