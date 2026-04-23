from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Company, Offer, PlayerProfile

User = get_user_model()


class OfferSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = Offer
        fields = [
            "id",
            "title",
            "company_name",
            "description",
            "offer_type",
            "discount_percent",
            "promo_code",
            "is_active",
            "starts_at",
            "expires_at",
            "created_at",
        ]


class CompanySerializer(serializers.ModelSerializer):
    offers_count = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "logo",
            "is_active",
            "offers_count",
        ]

    def get_offers_count(self, obj):
        return obj.offers.filter(is_active=True).count()


class CompanyDetailSerializer(CompanySerializer):
    offers = OfferSerializer(many=True, read_only=True)

    class Meta(CompanySerializer.Meta):
        fields = CompanySerializer.Meta.fields + ["offers"]


class LeaderboardSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)

    class Meta:
        model = PlayerProfile
        fields = [
            "rank",
            "score",
            "username",
            "first_name",
            "last_name",
            "updated_at",
        ]