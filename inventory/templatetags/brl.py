from decimal import Decimal

from django import template

from inventory.money import cents_to_brl

register = template.Library()


@register.filter
def brl(cents):
    """119990 -> R$ 1.199,90"""
    return cents_to_brl(cents)


@register.filter
def pct(value, decimals=1):
    """Decimal('38.50') -> 38,5%"""
    if value is None or value == "":
        return "—"
    casas = int(decimals)
    numero = Decimal(str(value))
    texto = f"{numero:.{casas}f}".replace(".", ",")
    return f"{texto}%"


@register.filter
def pct_signed(value, decimals=1):
    """Mostra sinal explícito: +38,5% / -12,0%"""
    if value is None or value == "":
        return "—"
    casas = int(decimals)
    numero = Decimal(str(value))
    sinal = "+" if numero > 0 else ""
    texto = f"{numero:.{casas}f}".replace(".", ",")
    return f"{sinal}{texto}%"


@register.filter
def dias(value):
    if value is None or value == "":
        return "—"
    return f"{int(value)} d"


@register.filter
def tone(value):
    """Classe de cor para valores monetários/percentuais."""
    if value is None or value == "":
        return "text-slate-500"
    return "text-emerald-600" if Decimal(str(value)) >= 0 else "text-rose-600"
