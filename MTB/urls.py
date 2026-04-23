# your_project_name/urls.py

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from liderbord.views import CompanyViewSet, OfferViewSet, LeaderboardViewSet, SubmitScoreView

router = DefaultRouter()
router.register("companies",   CompanyViewSet,     basename="company")
router.register("offers",      OfferViewSet,       basename="offer")
router.register("leaderboard", LeaderboardViewSet, basename="leaderboard")

urlpatterns = [
    path("admin/",                        admin.site.urls),
    path("api/",                          include(router.urls)),
    path("api/leaderboard/submit/",       SubmitScoreView.as_view(), name="submit-score"),
]