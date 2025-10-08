# web/authapp/api.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Invite

class RegisterWithInviteView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        token = request.data.get("invite_token")
        tele_id = request.data.get("tele_id")
        username = request.data.get("username", "")
        if not token:
            return Response({"error": "Invite token required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            invite = Invite.objects.get(token=token)
        except Invite.DoesNotExist:
            return Response({"error": "Invalid invite token"}, status=status.HTTP_400_BAD_REQUEST)

        if not invite.is_valid():
            return Response({"error": "Invite token expired or already used"}, status=status.HTTP_400_BAD_REQUEST)

        # Создаём пользователя с ролью из invite; is_verified=False (ждёт проверки)
        user, created = User.objects.get_or_create(tele_id=tele_id, defaults={"username": username, "role": invite.role})
        if not created:
            return Response({"error": "User already exists"}, status=status.HTTP_400_BAD_REQUEST)

        # отметим invite как использованный
        invite.used = True
        invite.used_by = user
        invite.save()

        # отдаём refresh/access — пользователь всё ещё не верифицирован, но имеет аккаунт
        refresh = RefreshToken.for_user(user)
        return Response({
            "user_id": user.id,
            "role": user.role,
            "is_verified": user.is_verified,
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        })


class ProfileView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "tele_id": user.tele_id,
            "role": user.role,
            "is_verified": user.is_verified,
        })
