"""Dados fictícios da conta demo — o recrutador precisa ver o app cheio."""

from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .models import Category, Item, Sale

DEMO_USERNAME = "demo"
DEMO_PASSWORD = "briquestats"

CATEGORIAS = [
    ("Eletrodomésticos", "azul"),
    ("PC & Hardware", "violeta"),
    ("Automotivo", "ambar"),
]

# nome, categoria, condição, custo (R$), referência (R$), dias desde a compra,
# venda = (dias desde a venda, preço, taxas, canal) | None
ITENS = [
    ("Air Fryer Mondial 4L", "Eletrodomésticos", "usado", 180, 320, 12, None),
    (
        "Geladeira Consul 340L",
        "Eletrodomésticos",
        "usado",
        900,
        1500,
        120,
        (95, 1450, 0, "olx"),
    ),
    (
        "Notebook Dell Inspiron 15",
        "PC & Hardware",
        "usado",
        1200,
        1900,
        90,
        (40, 1850, 90, "mercado_livre"),
    ),
    ("Placa de vídeo RTX 3060", "PC & Hardware", "usado", 1100, 1600, 25, None),
    (
        "Kit memória RAM 16GB",
        "PC & Hardware",
        "novo",
        150,
        260,
        60,
        (45, 250, 0, "mercado_livre"),
    ),
    ("Farol do Corolla 2020", "Automotivo", "usado", 320, 550, 18, None),
    ("Roda aro 17 original", "Automotivo", "usado", 700, 1200, 40, None),
    (
        "Micro-ondas Electrolux 20L",
        "Eletrodomésticos",
        "usado",
        220,
        400,
        35,
        (20, 390, 0, "olx"),
    ),
    ("Monitor LG 24\"", "PC & Hardware", "usado", 380, 650, 15, None),
    (
        "Bateria Moura 60Ah",
        "Automotivo",
        "novo",
        280,
        480,
        150,
        (130, 470, 0, "feira"),
    ),
    ("Liquidificador Philips", "Eletrodomésticos", "usado", 90, 180, 8, None),
    ("Teclado mecânico Redragon", "PC & Hardware", "usado", 130, 240, 22, None),
    ("Lanterna traseira Civic", "Automotivo", "usado", 180, 320, 30, None),
    ("Cafeteira Nespresso", "Eletrodomésticos", "usado", 250, 450, 5, None),
    ("SSD 1TB Kingston", "PC & Hardware", "novo", 280, 450, 10, None),
]


@transaction.atomic
def seed_demo_data(user, *, reset: bool = False) -> None:
    if reset:
        user.items.all().delete()
        user.categories.all().delete()
    elif user.items.exists():
        return

    hoje = timezone.localdate()
    categorias = {
        nome: Category.objects.create(user=user, name=nome, color=cor)
        for nome, cor in CATEGORIAS
    }

    for (
        nome,
        categoria,
        condicao,
        custo,
        referencia,
        dias_compra,
        venda,
    ) in ITENS:
        item = Item.objects.create(
            user=user,
            category=categorias[categoria],
            name=nome,
            condition=condicao,
            cost_cents=custo * 100,
            reference_cents=referencia * 100,
            acquired_on=hoje - timedelta(days=dias_compra),
        )
        if venda is not None:
            dias_venda, preco, taxas, canal = venda
            Sale.objects.create(
                item=item,
                price_cents=preco * 100,
                fees_cents=taxas * 100,
                channel=canal,
                sold_on=hoje - timedelta(days=dias_venda),
            )


def ensure_demo_user():
    """Garante que a conta demo exista e tenha dados. Usada pelo botão de login."""
    Usuario = get_user_model()
    usuario, criado = Usuario.objects.get_or_create(
        username=DEMO_USERNAME,
        defaults={"email": "demo@briquestats.app"},
    )
    if criado:
        usuario.set_password(DEMO_PASSWORD)
        usuario.save()
    if not usuario.items.exists():
        seed_demo_data(usuario)
    return usuario
