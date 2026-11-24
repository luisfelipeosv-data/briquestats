"""Cálculos puros do domínio.

Nenhuma função aqui toca no banco: recebem objetos (ou None) e devolvem números.
Isso mantém os testes rápidos e as regras em um único lugar.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, DivisionByZero, InvalidOperation

HUNDRED = Decimal(100)


def ratio_percent(numerator: int | Decimal, denominator: int | Decimal) -> Decimal | None:
    """(numerator / denominator) * 100 com 2 casas. None quando o denominador é zero."""
    if not denominator:
        return None
    try:
        return (Decimal(numerator) / Decimal(denominator) * HUNDRED).quantize(
            Decimal("0.01")
        )
    except (DivisionByZero, InvalidOperation):
        return None


def profit_cents(sale) -> int | None:
    """Lucro real = valor de venda - taxas - custo de aquisição."""
    if sale is None:
        return None
    return sale.price_cents - sale.fees_cents - sale.item.cost_cents


def roi(sale) -> Decimal | None:
    """Retorno sobre o capital investido, em %."""
    if sale is None:
        return None
    return ratio_percent(profit_cents(sale), sale.item.cost_cents)


def margin(sale) -> Decimal | None:
    """Margem sobre a receita, em %."""
    if sale is None:
        return None
    return ratio_percent(profit_cents(sale), sale.price_cents)


def premium_vs_reference(sale) -> Decimal | None:
    """Quanto a venda ficou acima/abaixo do preço de referência, em %."""
    if sale is None or not sale.item.reference_cents:
        return None
    diferenca = sale.price_cents - sale.item.reference_cents
    return ratio_percent(diferenca, sale.item.reference_cents)


def discount_vs_reference(item) -> Decimal | None:
    """Quanto o custo ficou abaixo do preço de referência, em % (comprou bem?)."""
    if item is None or not item.reference_cents:
        return None
    economia = item.reference_cents - item.cost_cents
    return ratio_percent(economia, item.reference_cents)


def days_held(item, today: date | None = None) -> int:
    """Dias entre a aquisição e a venda (ou hoje, se ainda em estoque)."""
    fim = today or date.today()
    sale = getattr(item, "sale", None)
    if sale is not None:
        fim = sale.sold_on
    return max((fim - item.acquired_on).days, 0)
