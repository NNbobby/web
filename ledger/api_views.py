from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal
from ledger.services import LedgerService
from authapp.models import User
from authapp.permissions import IsVerified
from rest_framework.permissions import IsAuthenticated

class TransferView(APIView):
    permission_classes = [IsAuthenticated, IsVerified]
    """POST /api/ledger/transfer/"""

    def post(self, request):
        try:
            from_id = request.data.get("from_id")
            to_id = request.data.get("to_id")
            amount = Decimal(request.data.get("amount"))
            description = request.data.get("description", "")

            from_user = User.objects.get(id=from_id)
            to_user = User.objects.get(id=to_id)

            LedgerService.transfer(from_user, to_user, amount, description)
            return Response({"message": "Перевод выполнен успешно"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class FreezeView(APIView):
    """POST /api/ledger/freeze/"""

    def post(self, request):
        try:
            user_id = request.data.get("user_id")
            amount = Decimal(request.data.get("amount"))
            description = request.data.get("description", "")

            user = User.objects.get(id=user_id)
            LedgerService.freeze(user, amount, description)
            return Response({"message": "Средства заморожены"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UnfreezeView(APIView):
    """POST /api/ledger/unfreeze/"""

    def post(self, request):
        try:
            user_id = request.data.get("user_id")
            amount = Decimal(request.data.get("amount"))
            description = request.data.get("description", "")

            user = User.objects.get(id=user_id)
            LedgerService.unfreeze(user, amount, description)
            return Response({"message": "Средства разморожены"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
