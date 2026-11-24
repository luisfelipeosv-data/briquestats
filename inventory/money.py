"""Helpers de dinheiro: tudo circula em centavos (int) para evitar float."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

PLACEHOLDER = "—"


def cents_to_brl(cents: int | None, *, symbol: bool = True) -> str:
    """119990 -> 'R$ 1.199,90'."""
    if cents is None:
        return PLACEHOLDER
    cents = int(cents)
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    reais, centavos = divmod(cents, 100)
    inteiro = f"{reais:,}".replace(",", ".")
    valor = f"{inteiro},{centavos:02d}"
    return f"{sign}{'R$ ' if symbol else ''}{valor}"


def cents_to_input(cents: int | None) -> str:
    """Formato usado dentro de inputs: '1.199,90' (sem R$)."""
    return "" if cents is None else cents_to_brl(cents, symbol=False)


def parse_brl_to_cents(raw: str | int | float | Decimal | None) -> int | None:
    """Aceita 'R$ 1.199,90', '1199,90', '1199.90', '1.199' e devolve centavos.

    Regras:
      - só vírgula  -> vírgula é decimal
      - só ponto    -> ponto é decimal, exceto '1.199' (milhar brasileiro)
      - ambos       -> ponto é milhar e vírgula é decimal
    """
    if raw is None:
        return None
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return raw * 100
    if isinstance(raw, (float, Decimal)):
        return int((Decimal(str(raw)) * 100).to_integral_value())

    texto = str(raw).strip()
    if not texto:
        return None

    for lixo in ("R$", "r$", "\u00a0", " "):
        texto = texto.replace(lixo, "")

    negativo = texto.startswith("-")
    texto = texto.lstrip("-+")
    if not texto:
        return None

    tem_virgula = "," in texto
    tem_ponto = "." in texto

    if tem_virgula and tem_ponto:
        # 1.199,90 -> ponto é milhar
        texto = texto.replace(".", "").replace(",", ".")
    elif tem_virgula:
        texto = texto.replace(",", ".")
    elif tem_ponto:
        partes = texto.split(".")
        if len(partes) == 2 and len(partes[1]) == 3 and len(partes[0]) <= 3:
            # '1.199' / '12.500' -> milhar
            texto = "".join(partes)
        elif len(partes) > 2:
            # 1.199.000 -> milhar
            texto = "".join(partes)

    try:
        valor = Decimal(texto)
    except (InvalidOperation, ValueError):
        return None

    centavos = int((valor * 100).to_integral_value())
    return -centavos if negativo else centavos
