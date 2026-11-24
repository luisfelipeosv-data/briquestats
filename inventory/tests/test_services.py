from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from inventory import services


def venda(custo=10000, preco=15000, taxas=0, referencia=None):
    item = SimpleNamespace(cost_cents=custo, reference_cents=referencia)
    return SimpleNamespace(
        price_cents=preco, fees_cents=taxas, item=item, sold_on=date(2026, 2, 1)
    )


def test_lucro_desconta_taxas():
    assert services.profit_cents(venda(custo=10000, preco=15000, taxas=1500)) == 3500


def test_roi_sobre_o_custo():
    # (15000 - 10000) / 10000 = 50%
    assert services.roi(venda()) == Decimal("50.00")


def test_margem_sobre_a_venda():
    # 5000 / 15000 = 33.33%
    assert services.margin(venda()) == Decimal("33.33")


def test_prejuizo_gera_roi_negativo():
    assert services.roi(venda(custo=10000, preco=8000)) == Decimal("-20.00")


def test_custo_zero_nao_divide_por_zero():
    assert services.roi(venda(custo=0, preco=5000)) is None
    assert services.margin(venda(custo=0, preco=0)) is None


def test_premium_vs_referencia():
    # vendeu 15000 com referência 12000 -> +25%
    assert services.premium_vs_reference(venda(preco=15000, referencia=12000)) == (
        Decimal("25.00")
    )
    assert services.premium_vs_reference(venda(referencia=None)) is None


def test_desconto_vs_referencia():
    item = SimpleNamespace(cost_cents=6000, reference_cents=10000)
    assert services.discount_vs_reference(item) == Decimal("40.00")
    assert services.discount_vs_reference(SimpleNamespace(cost_cents=1, reference_cents=None)) is None


def test_dias_parado_usa_hoje_quando_nao_vendido():
    item = SimpleNamespace(acquired_on=date(2026, 1, 1), sale=None)
    assert services.days_held(item, today=date(2026, 1, 31)) == 30


def test_dias_ate_vender_usa_data_da_venda():
    item = SimpleNamespace(
        acquired_on=date(2026, 1, 1),
        sale=SimpleNamespace(sold_on=date(2026, 1, 11)),
    )
    assert services.days_held(item, today=date(2026, 6, 1)) == 10


def test_dias_nunca_negativo():
    item = SimpleNamespace(acquired_on=date(2026, 2, 1), sale=None)
    assert services.days_held(item, today=date(2026, 1, 1)) == 0


def test_sem_venda_nao_tem_lucro():
    assert services.profit_cents(None) is None
    assert services.roi(None) is None
