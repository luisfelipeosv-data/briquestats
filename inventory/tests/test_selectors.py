from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from inventory import selectors
from inventory.models import Item, Sale


@pytest.fixture
def cenario(usuario, categoria):
    hoje = timezone.localdate()
    vendido = Item.objects.create(
        user=usuario,
        category=categoria,
        name="SSD",
        cost_cents=10000,
        acquired_on=hoje - timedelta(days=30),
    )
    Sale.objects.create(
        item=vendido,
        price_cents=15000,
        fees_cents=0,
        channel="olx",
        sold_on=hoje,
    )
    Item.objects.create(
        user=usuario,
        category=categoria,
        name="Monitor",
        cost_cents=20000,
        acquired_on=hoje - timedelta(days=10),
    )
    return usuario


@pytest.mark.django_db
def test_metricas_do_dashboard(cenario):
    metricas = selectors.dashboard_metrics(cenario)
    assert metricas.stock_cents == 20000
    assert metricas.stock_count == 1
    assert metricas.realized_profit_cents == 5000
    assert metricas.revenue_cents == 15000
    assert metricas.roi == Decimal("50.00")
    assert metricas.sold_count == 1
    assert metricas.avg_days_held == 30.0


@pytest.mark.django_db
def test_serie_mensal_tem_doze_meses(cenario):
    serie = selectors.monthly_profit(cenario)
    assert len(serie) == 12
    assert serie[-1]["profit"] == 5000
    assert serie[-1]["count"] == 1


@pytest.mark.django_db
def test_roi_por_categoria(cenario):
    linhas = selectors.roi_by_category(cenario)
    assert len(linhas) == 1
    assert linhas[0]["name"] == "PC & Hardware"
    assert linhas[0]["profit"] == 5000
    assert linhas[0]["roi"] == Decimal("50.00")


@pytest.mark.django_db
def test_metricas_sao_isoladas_por_usuario(outro_usuario):
    metricas = selectors.dashboard_metrics(outro_usuario)
    assert metricas.stock_cents == 0
    assert metricas.sold_count == 0
    assert metricas.roi is None
    assert selectors.monthly_profit(outro_usuario)[-1]["profit"] == 0
    assert selectors.roi_by_category(outro_usuario) == []
