from decimal import Decimal

import pytest

from inventory.money import cents_to_brl, parse_brl_to_cents


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("1.199,90", 119990),
        ("R$ 1.199,90", 119990),
        ("R$1.199,90", 119990),
        ("1199,90", 119990),
        ("1199.90", 119990),
        ("1.199", 119900),
        ("12.500", 1250000),
        ("1.234.567,89", 123456789),
        ("0,50", 50),
        ("0", 0),
        ("", None),
        ("   ", None),
        (None, None),
        ("abc", None),
        ("R$", None),
    ],
)
def test_parse_brl_to_cents(entrada, esperado):
    assert parse_brl_to_cents(entrada) == esperado


def test_parse_aceita_numero():
    assert parse_brl_to_cents(12) == 1200
    assert parse_brl_to_cents(Decimal("12.50")) == 1250


@pytest.mark.parametrize(
    ("centavos", "esperado"),
    [
        (119990, "R$ 1.199,90"),
        (0, "R$ 0,00"),
        (50, "R$ 0,50"),
        (123456789, "R$ 1.234.567,89"),
        (None, "—"),
        (-1500, "-R$ 15,00"),
    ],
)
def test_cents_to_brl(centavos, esperado):
    assert cents_to_brl(centavos) == esperado


@pytest.mark.parametrize("valor", ["1.199,90", "1199,90", "1199.90"])
def test_ida_e_volta(valor):
    centavos = parse_brl_to_cents(valor)
    assert parse_brl_to_cents(cents_to_brl(centavos, symbol=False)) == centavos
