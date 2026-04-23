from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import F, Window
from django.db.models.functions import Rank

User = get_user_model()


class PlayerProfile(models.Model):
    """
    Профиль игрока — расширяет стандартного User.
    score и rank обновляются на месте, новые записи не создаются.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Пользователь",
    )
    score = models.PositiveIntegerField(default=0, verbose_name="Очки")
    rank = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Место в рейтинге"
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        verbose_name = "Профиль игрока"
        verbose_name_plural = "Профили игроков"
        ordering = ["rank", "-score"]

    def __str__(self):
        return f"#{self.rank} {self.user.username} — {self.score} очков"

    def update_score(self, new_score: int) -> bool:
        """
        Обновить score только если новый результат лучше предыдущего.
        Возвращает True если счёт обновлён, False если нет.
        """
        if new_score <= self.score:
            return False

        self.score = new_score
        self.save(update_fields=["score", "updated_at"])
        PlayerProfile.recalculate_ranks()
        return True

    @classmethod
    def recalculate_ranks(cls) -> None:
        """
        Пересчитать rank для всех игроков на основе текущего score.
        Использует оконную функцию RANK() — один запрос к БД.
        """
        ranked = (
            cls.objects.annotate(
                new_rank=Window(
                    expression=Rank(),
                    order_by=F("score").desc(),
                )
            )
        )
        # Bulk-update: обновляем только изменившиеся ранги
        updates = []
        for profile in ranked:
            if profile.rank != profile.new_rank:
                profile.rank = profile.new_rank
                updates.append(profile)

        if updates:
            cls.objects.bulk_update(updates, fields=["rank"])


class Company(models.Model):
    """Таблица компаний"""

    name = models.CharField(max_length=255, verbose_name="Название компании")
    slug = models.SlugField(unique=True, verbose_name="URL-идентификатор")
    logo = models.ImageField(
        upload_to="companies/logos/",
        null=True,
        blank=True,
        verbose_name="Логотип",
    )
    description = models.TextField(blank=True, verbose_name="Описание")
    website = models.URLField(blank=True, verbose_name="Сайт")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Компания"
        verbose_name_plural = "Компании"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Offer(models.Model):
    """Предложения/бонусы — многие к одной компании"""

    class OfferType(models.TextChoices):
        DISCOUNT = "discount", "Скидка"
        CASHBACK = "cashback", "Кэшбэк"
        GIFT = "gift", "Подарок"
        PROMO = "promo", "Промокод"
        OTHER = "other", "Другое"

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="offers",
        verbose_name="Компания",
    )
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    description = models.TextField(verbose_name="Описание предложения")
    offer_type = models.CharField(
        max_length=20,
        choices=OfferType.choices,
        default=OfferType.OTHER,
        verbose_name="Тип предложения",
    )
    discount_percent = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name="Скидка (%)",
    )
    promo_code = models.CharField(max_length=50, blank=True, verbose_name="Промокод")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    starts_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата начала")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата окончания")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Предложение"
        verbose_name_plural = "Предложения"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.company.name} — {self.title}"