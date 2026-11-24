from __future__ import annotations

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from . import services


class Category(models.Model):
    """Tipo de produto do usuário (Eletrodomésticos, PC, Automotivo...)."""

    COLOR_CHOICES = [
        ("azul", "Azul"),
        ("ciano", "Ciano"),
        ("verde", "Verde"),
        ("lima", "Lima"),
        ("ambar", "Âmbar"),
        ("laranja", "Laranja"),
        ("rosa", "Rosa"),
        ("violeta", "Violeta"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categories",
    )
    name = models.CharField("nome", max_length=60)
    color = models.CharField(
        "cor", max_length=20, choices=COLOR_CHOICES, default="azul"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "categoria"
        verbose_name_plural = "categorias"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"], name="unique_category_name_per_user"
            )
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def item_count(self) -> int:
        return self.items.count()


class Item(models.Model):
    """Uma peça comprada para revenda."""

    class Condition(models.TextChoices):
        NEW = "novo", "Novo"
        USED = "usado", "Usado"
        FAULTY = "defeito", "Com defeito"

    class Status(models.TextChoices):
        IN_STOCK = "estoque", "Em estoque"
        SOLD = "vendido", "Vendido"
        ARCHIVED = "arquivado", "Arquivado"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="items",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items",
    )
    name = models.CharField("nome", max_length=120)
    condition = models.CharField(
        "condição", max_length=20, choices=Condition.choices, default=Condition.USED
    )
    cost_cents = models.PositiveIntegerField("quanto foi pago (centavos)")
    reference_cents = models.PositiveIntegerField(
        "preço de referência (centavos)", null=True, blank=True
    )
    acquired_on = models.DateField("data de aquisição", default=timezone.localdate)
    status = models.CharField(
        "status", max_length=20, choices=Status.choices, default=Status.IN_STOCK
    )
    notes = models.TextField("observações", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-acquired_on", "-id"]
        verbose_name = "item"
        verbose_name_plural = "itens"
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "category"]),
        ]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("item_detail", args=[self.pk])

    # -- atalhos de leitura --------------------------------------------------
    @property
    def sale(self) -> Sale | None:
        try:
            return self.sales  # reverse OneToOne
        except Sale.DoesNotExist:
            return None

    @property
    def is_sold(self) -> bool:
        return self.status == self.Status.SOLD

    @property
    def profit_cents(self) -> int | None:
        sale = self.sale
        return services.profit_cents(sale) if sale else None

    @property
    def roi(self):
        sale = self.sale
        return services.roi(sale) if sale else None

    @property
    def margin(self):
        sale = self.sale
        return services.margin(sale) if sale else None

    @property
    def premium_vs_reference(self):
        sale = self.sale
        return services.premium_vs_reference(sale) if sale else None

    @property
    def discount_vs_reference(self):
        return services.discount_vs_reference(self)

    @property
    def days_held(self) -> int:
        return services.days_held(self)


class Sale(models.Model):
    """Venda de um item (1:1). Existe separada para permitir desfazer e manter histórico."""

    class Channel(models.TextChoices):
        OLX = "olx", "OLX"
        MERCADO_LIVRE = "mercado_livre", "Mercado Livre"
        FEIRA = "feira", "Feira / brique"
        OUTRO = "outro", "Outro"

    item = models.OneToOneField(
        Item, on_delete=models.CASCADE, related_name="sales", verbose_name="item"
    )
    price_cents = models.PositiveIntegerField("valor de venda (centavos)")
    fees_cents = models.PositiveIntegerField("taxas (centavos)", default=0)
    channel = models.CharField(
        "canal", max_length=20, choices=Channel.choices, default=Channel.OLX
    )
    sold_on = models.DateField("data da venda", default=timezone.localdate)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-sold_on", "-id"]
        verbose_name = "venda"
        verbose_name_plural = "vendas"
        indexes = [models.Index(fields=["sold_on"])]

    def __str__(self) -> str:
        return f"Venda de {self.item.name}"

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.item_id and self.price_cents is not None:
            if self.price_cents == 0:
                raise ValidationError(
                    {"price_cents": "O valor da venda precisa ser maior que zero."}
                )
            if self.sold_on and self.item.acquired_on and self.sold_on < self.item.acquired_on:
                raise ValidationError(
                    {"sold_on": "A venda não pode ser anterior à aquisição."}
                )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        Item.objects.filter(pk=self.item_id).exclude(
            status=Item.Status.SOLD
        ).update(status=Item.Status.SOLD, updated_at=timezone.now())

    def delete(self, *args, **kwargs):
        item_id = self.item_id
        super().delete(*args, **kwargs)
        Item.objects.filter(pk=item_id, status=Item.Status.SOLD).update(
            status=Item.Status.IN_STOCK, updated_at=timezone.now()
        )

    # -- métricas ------------------------------------------------------------
    @property
    def profit_cents(self) -> int:
        return services.profit_cents(self)

    @property
    def roi(self):
        return services.roi(self)

    @property
    def margin(self):
        return services.margin(self)

    @property
    def premium_vs_reference(self):
        return services.premium_vs_reference(self)
