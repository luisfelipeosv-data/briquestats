"""Consultas e agregações.

Cards usam agregação no banco. Séries de gráfico são montadas em Python porque o
volume é pequeno (uma pessoa, dezenas de itens) e isso mantém o código portátil
entre SQLite e Postgres.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.db.models import Avg, Count, Sum
from django.utils import timezone

from .models import Category, Item, Sale
from .services import ratio_percent

MONTHS_PT = [
    "jan",
    "fev",
    "mar",
    "abr",
    "mai",
    "jun",
    "jul",
    "ago",
    "set",
    "out",
    "nov",
    "dez",
]


@dataclass
class DashboardMetrics:
    stock_cents: int = 0
    stock_count: int = 0
    realized_profit_cents: int = 0
    revenue_cents: int = 0
    roi: Decimal | None = None
    sold_count: int = 0
    avg_ticket_cents: int = 0
    avg_days_held: float | None = None
    archived_count: int = 0


def _add_months(base: date, delta: int) -> date:
    total = base.year * 12 + (base.month - 1) + delta
    return date(total // 12, total % 12 + 1, 1)


def dashboard_metrics(user) -> DashboardMetrics:
    estoque = Item.objects.filter(user=user, status=Item.Status.IN_STOCK).aggregate(
        total=Sum("cost_cents"), quantidade=Count("id")
    )
    vendas = Sale.objects.filter(item__user=user).aggregate(
        receita=Sum("price_cents"),
        taxas=Sum("fees_cents"),
        custo=Sum("item__cost_cents"),
        quantidade=Count("id"),
        ticket=Avg("price_cents"),
    )

    receita = vendas["receita"] or 0
    taxas = vendas["taxas"] or 0
    custo = vendas["custo"] or 0
    lucro = receita - taxas - custo

    itens_vendidos = Item.objects.filter(
        user=user, status=Item.Status.SOLD
    ).select_related("sales")
    giros = [(item.sales.sold_on - item.acquired_on).days for item in itens_vendidos]

    return DashboardMetrics(
        stock_cents=estoque["total"] or 0,
        stock_count=estoque["quantidade"] or 0,
        realized_profit_cents=lucro,
        revenue_cents=receita,
        roi=ratio_percent(lucro, custo),
        sold_count=vendas["quantidade"] or 0,
        avg_ticket_cents=int(vendas["ticket"] or 0),
        avg_days_held=round(sum(giros) / len(giros), 1) if giros else None,
        archived_count=Item.objects.filter(
            user=user, status=Item.Status.ARCHIVED
        ).count(),
    )


def monthly_profit(user, months: int = 12) -> list[dict]:
    """Série dos últimos N meses (incluindo o atual), com meses vazios zerados."""
    hoje = timezone.localdate()
    inicio = _add_months(hoje, -(months - 1))

    buckets: dict[tuple[int, int], dict] = {}
    cursor = inicio
    for _ in range(months):
        buckets[(cursor.year, cursor.month)] = {
            "label": f"{MONTHS_PT[cursor.month - 1]}/{str(cursor.year)[2:]}",
            "profit": 0,
            "revenue": 0,
            "count": 0,
        }
        cursor = _add_months(cursor, 1)

    vendas = Sale.objects.filter(item__user=user, sold_on__gte=inicio).select_related(
        "item"
    )
    for venda in vendas:
        chave = (venda.sold_on.year, venda.sold_on.month)
        if chave not in buckets:
            continue
        bucket = buckets[chave]
        bucket["profit"] += venda.profit_cents
        bucket["revenue"] += venda.price_cents
        bucket["count"] += 1

    return list(buckets.values())


def roi_by_category(user) -> list[dict]:
    """ROI ponderado por custo, agrupado por categoria (só categorias com venda)."""
    acumulado: dict[int, dict] = {}

    vendas = Sale.objects.filter(item__user=user).select_related("item__category")
    for venda in vendas:
        categoria = venda.item.category
        chave = categoria.pk if categoria else 0
        linha = acumulado.setdefault(
            chave,
            {
                "name": categoria.name if categoria else "Sem categoria",
                "color": categoria.color if categoria else "azul",
                "profit": 0,
                "cost": 0,
                "count": 0,
            },
        )
        linha["profit"] += venda.profit_cents
        linha["cost"] += venda.item.cost_cents
        linha["count"] += 1

    linhas = list(acumulado.values())
    for linha in linhas:
        linha["roi"] = ratio_percent(linha["profit"], linha["cost"])
        linha["roi_float"] = float(linha["roi"]) if linha["roi"] is not None else 0.0
    linhas.sort(key=lambda item: item["profit"], reverse=True)
    return linhas


def category_options(user) -> list[Category]:
    return Category.objects.filter(user=user).annotate(
        total_itens=Count("items")
    )


def stock_by_category(user) -> list[dict]:
    """Capital parado por categoria (para a lista de categorias)."""
    linhas = (
        Item.objects.filter(user=user, status=Item.Status.IN_STOCK)
        .values("category_id", "category__name", "category__color")
        .annotate(total=Sum("cost_cents"), quantidade=Count("id"))
        .order_by("-total")
    )
    return list(linhas)


def top_items_by_profit(user, limit: int = 5) -> list[Item]:
    itens = (
        Item.objects.filter(user=user, status=Item.Status.SOLD)
        .select_related("category", "sales")
    )
    return sorted(itens, key=lambda item: item.profit_cents or 0, reverse=True)[:limit]


def recent_items(user, limit: int = 5) -> list[Item]:
    return list(
        Item.objects.filter(user=user)
        .select_related("category", "sales")
        .order_by("-created_at")[:limit]
    )


def recent_sales(user, limit: int = 5) -> list[Sale]:
    return list(
        Sale.objects.filter(item__user=user)
        .select_related("item", "item__category")
        .order_by("-sold_on", "-id")[:limit]
    )
