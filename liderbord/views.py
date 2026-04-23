from rest_framework import viewsets, filters, generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Company, Offer, PlayerProfile
from .serializers import (
    CompanySerializer,
    CompanyDetailSerializer,
    OfferSerializer,
    LeaderboardSerializer,
)


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.filter(is_active=True).prefetch_related("offers")
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CompanyDetailSerializer
        return CompanySerializer

    @action(detail=True, methods=["get"])
    def offers(self, request, pk=None):
        company = self.get_object()
        serializer = OfferSerializer(
            company.offers.filter(is_active=True), many=True
        )
        return Response(serializer.data)


class OfferViewSet(viewsets.ModelViewSet):
    queryset = Offer.objects.filter(is_active=True).select_related("company")
    serializer_class = OfferSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["company", "offer_type"]
    ordering_fields = ["created_at", "discount_percent"]


class SubmitScoreView(generics.GenericAPIView):
    """
    POST /leaderboard/submit/
    Body: { "score": 1500 }
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        new_score = request.data.get("score")

        if new_score is None:
            return Response(
                {"detail": "Поле score обязательно."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            new_score = int(new_score)
        except (TypeError, ValueError):
            return Response(
                {"detail": "score должен быть целым числом."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile, _ = PlayerProfile.objects.get_or_create(user=request.user)
        updated = profile.update_score(new_score)

        return Response(
            {
                "updated": updated,
                "score": profile.score,
                "rank": profile.rank,
            },
            status=status.HTTP_200_OK,
        )


class LeaderboardViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /leaderboard/      — рейтинг всех игроков, отсортирован по rank
    GET /leaderboard/{id}/ — профиль конкретного игрока
    """

    queryset = PlayerProfile.objects.select_related("user").order_by("rank", "-score")
    serializer_class = LeaderboardSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["user__username", "user__first_name", "user__last_name"]


