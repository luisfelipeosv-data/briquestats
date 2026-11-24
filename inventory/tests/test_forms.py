from datetime import date

import pytest
from django.db import IntegrityError, transaction

from inventory.forms import BRLCentsField, CategoryForm, ItemForm, SaleForm


def test_campo_moeda_converte_para_centavos():
    campo = BRLCentsField()
    assert campo.clean("R$ 1.199,90") == 119990
    assert campo.clean("1199,90") == 119990


def test_campo_moeda_aceita_vazio_quando_opcional():
    campo = BRLCentsField(required=False)
    assert campo.clean("") is None


def test_campo_moeda_rejeita_texto():
    campo = BRLCentsField()
    try:
        campo.clean("muito caro")
    except Exception as erro:
        assert "válido" in str(erro)
    else:  # pragma: no cover
        raise AssertionError("deveria ter falhado")


def test_item_form_grava_em_centavos(usuario, categoria):
    form = ItemForm(
        data={
            "name": "Air Fryer",
            "category": categoria.pk,
            "condition": "usado",
            "cost_cents": "180,00",
            "reference_cents": "320,00",
            "acquired_on": "2026-01-10",
            "notes": "",
        },
        user=usuario,
    )
    assert form.is_valid(), form.errors
    item = form.save(commit=False)
    assert item.cost_cents == 18000
    assert item.reference_cents == 32000


def test_item_form_exige_custo_positivo(usuario):
    form = ItemForm(
        data={
            "name": "Peça",
            "category": "",
            "condition": "usado",
            "cost_cents": "0,00",
            "reference_cents": "",
            "acquired_on": "2026-01-10",
            "notes": "",
        },
        user=usuario,
    )
    assert not form.is_valid()
    assert "cost_cents" in form.errors


def test_categoria_unica_por_usuario(usuario, categoria):
    form = CategoryForm(data={"name": categoria.name, "color": "verde"})
    assert form.is_valid()  # o form não sabe do usuário
    categoria_dup = form.save(commit=False)
    categoria_dup.user = usuario
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            categoria_dup.save()


def test_sale_form_valida_taxas_maiores_que_venda(item):
    form = SaleForm(
        data={
            "price_cents": "100,00",
            "fees_cents": "150,00",
            "channel": "olx",
            "sold_on": date.today().isoformat(),
        },
        item=item,
    )
    assert not form.is_valid()
    assert "fees_cents" in form.errors


def test_sale_form_rejeita_venda_antes_da_compra(item):
    form = SaleForm(
        data={
            "price_cents": "400,00",
            "fees_cents": "0,00",
            "channel": "olx",
            "sold_on": "2025-12-01",  # item foi adquirido em 2026-01-01
        },
        item=item,
    )
    assert not form.is_valid()
    assert "sold_on" in form.errors
