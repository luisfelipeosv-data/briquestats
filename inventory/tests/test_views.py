from datetime import date
from decimal import Decimal

import pytest
from django.urls import reverse

from inventory.models import Item, Sale


def test_paginas_exigem_login(client):
    for url in ["/", "/itens/", "/vendas/", "/categorias/", "/itens/novo/"]:
        resposta = client.get(url)
        assert resposta.status_code == 302
        assert "/entrar/" in resposta["Location"]


def test_dashboard_abre(cliente):
    assert cliente.get("/").status_code == 200


def test_cria_item_com_moeda_brasileira(cliente, usuario, categoria):
    resposta = cliente.post(
        reverse("item_create"),
        {
            "name": "Air Fryer Mondial",
            "category": categoria.pk,
            "condition": "usado",
            "cost_cents": "R$ 180,00",
            "reference_cents": "320,00",
            "acquired_on": "2026-01-10",
            "notes": "",
        },
    )
    assert resposta.status_code == 302
    item = Item.objects.get(name="Air Fryer Mondial")
    assert item.user == usuario
    assert item.cost_cents == 18000
    assert item.status == Item.Status.IN_STOCK


def test_venda_marca_item_e_calcula_metricas(cliente, item):
    resposta = cliente.post(
        reverse("sale_create", args=[item.pk]),
        {
            "price_cents": "450,00",
            "fees_cents": "20,00",
            "channel": "olx",
            "sold_on": "2026-02-01",
        },
    )
    assert resposta.status_code == 302
    item.refresh_from_db()
    assert item.status == Item.Status.SOLD
    venda = Sale.objects.get(item=item)
    assert venda.profit_cents == 15000  # 45000 - 2000 - 28000
    assert venda.roi == Decimal("53.57")


def test_nao_vende_item_antes_da_aquisicao(cliente, item):
    cliente.post(
        reverse("sale_create", args=[item.pk]),
        {
            "price_cents": "450,00",
            "fees_cents": "0,00",
            "channel": "olx",
            "sold_on": "2025-12-01",
        },
    )
    item.refresh_from_db()
    assert item.status == Item.Status.IN_STOCK
    assert not Sale.objects.filter(item=item).exists()


def test_desfazer_venda_devolve_ao_estoque(cliente, item):
    cliente.post(
        reverse("sale_create", args=[item.pk]),
        {
            "price_cents": "450,00",
            "fees_cents": "0,00",
            "channel": "olx",
            "sold_on": "2026-02-01",
        },
    )
    venda = Sale.objects.get(item=item)
    cliente.post(reverse("sale_delete", args=[venda.pk]))
    item.refresh_from_db()
    assert item.status == Item.Status.IN_STOCK
    assert not Sale.objects.filter(item=item).exists()


def test_nao_remove_item_vendido(cliente, item):
    Sale.objects.create(
        item=item,
        price_cents=45000,
        fees_cents=0,
        channel="olx",
        sold_on=date(2026, 2, 1),
    )
    cliente.post(reverse("item_delete", args=[item.pk]))
    assert Item.objects.filter(pk=item.pk).exists()


def test_remove_item_nao_vendido(cliente, item):
    cliente.post(reverse("item_delete", args=[item.pk]))
    assert not Item.objects.filter(pk=item.pk).exists()


def test_usuario_nao_acessa_item_de_outro(cliente, outro_usuario, item):
    outro_item = Item.objects.create(
        user=outro_usuario,
        name="Item secreto",
        cost_cents=1000,
        acquired_on=date(2026, 1, 1),
    )
    assert cliente.get(reverse("item_detail", args=[outro_item.pk])).status_code == 404
    assert cliente.get(reverse("item_update", args=[outro_item.pk])).status_code == 404

    listagem = cliente.get(reverse("item_list"))
    assert b"Item secreto" not in listagem.content


def test_usuario_nao_vende_item_de_outro(cliente, outro_usuario):
    alheio = Item.objects.create(
        user=outro_usuario,
        name="Item do Bruno",
        cost_cents=1000,
        acquired_on=date(2026, 1, 1),
    )
    resposta = cliente.post(
        reverse("sale_create", args=[alheio.pk]),
        {
            "price_cents": "1,00",
            "fees_cents": "0,00",
            "channel": "olx",
            "sold_on": "2026-02-01",
        },
    )
    assert resposta.status_code == 404
    assert not Sale.objects.filter(item=alheio).exists()


def test_filtro_de_busca(cliente, usuario, item):
    Item.objects.create(
        user=usuario,
        name="Geladeira Consul",
        cost_cents=90000,
        acquired_on=date(2026, 1, 1),
    )
    resposta = cliente.get(reverse("item_list"), {"q": "geladeira"})
    assert b"Geladeira Consul" in resposta.content
    assert b"SSD 1TB" not in resposta.content


def test_filtro_por_status(cliente, item):
    Sale.objects.create(
        item=item,
        price_cents=45000,
        fees_cents=0,
        channel="olx",
        sold_on=date(2026, 2, 1),
    )
    resposta = cliente.get(reverse("item_list"), {"status": "estoque"})
    assert b"SSD 1TB" not in resposta.content

    resposta = cliente.get(reverse("item_list"), {"status": "vendido"})
    assert b"SSD 1TB" in resposta.content


def test_htmx_devolve_apenas_o_painel(cliente, item):
    resposta = cliente.get(reverse("item_list"), HTTP_HX_REQUEST="true")
    assert resposta.status_code == 200
    assert b"<html" not in resposta.content
    assert b'id="inventory-panel"' in resposta.content


@pytest.mark.django_db
def test_preview_de_venda(cliente, item):
    resposta = cliente.post(
        reverse("sale_preview", args=[item.pk]),
        {"price_cents": "450,00", "fees_cents": "20,00"},
        HTTP_HX_REQUEST="true",
    )
    assert resposta.status_code == 200
    assert b"150,00" in resposta.content  # lucro 450 - 20 - 280


def test_cria_categoria(cliente, usuario):
    cliente.post(reverse("category_list"), {"name": "Automotivo", "color": "ambar"})
    assert usuario.categories.filter(name="Automotivo").exists()


def test_categoria_de_outro_usuario_da_404(cliente, outro_usuario):
    from inventory.models import Category

    alheia = Category.objects.create(user=outro_usuario, name="Alheia")
    assert cliente.get(reverse("category_update", args=[alheia.pk])).status_code == 404


def test_health(client):
    resposta = client.get("/health/")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}
