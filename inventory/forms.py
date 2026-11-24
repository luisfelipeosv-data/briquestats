from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError
from django.urls import reverse

from config.ui import StyledFormMixin

from .models import Category, Item, Sale
from .money import cents_to_input, parse_brl_to_cents


class BRLCentsField(forms.Field):
    """Campo de texto que aceita 'R$ 1.199,90' e entrega centavos (int)."""

    widget = forms.TextInput(
        attrs={
            "inputmode": "decimal",
            "autocomplete": "off",
            "placeholder": "0,00",
        }
    )
    default_error_messages = {
        "invalid": "Informe um valor válido, como 1.199,90.",
        "negative": "O valor não pode ser negativo.",
    }

    def to_python(self, value):
        if value in self.empty_values:
            return None
        centavos = parse_brl_to_cents(value)
        if centavos is None:
            raise ValidationError(
                self.error_messages["invalid"], code="invalid_money"
            )
        if centavos < 0:
            raise ValidationError(
                self.error_messages["negative"], code="negative_money"
            )
        return centavos

    def prepare_value(self, value):
        if isinstance(value, int):
            return cents_to_input(value)
        return value

    def has_changed(self, initial, data):
        try:
            return self.to_python(data) != initial
        except ValidationError:
            return True


class ItemForm(StyledFormMixin, forms.ModelForm):
    cost_cents = BRLCentsField(label="Quanto você pagou")
    reference_cents = BRLCentsField(
        label="Preço de referência (mercado)", required=False
    )

    class Meta:
        model = Item
        fields = [
            "name",
            "category",
            "condition",
            "cost_cents",
            "reference_cents",
            "acquired_on",
            "notes",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={"placeholder": "Ex.: Air Fryer Mondial 4L", "autofocus": True}
            ),
            "acquired_on": forms.DateInput(
                format="%Y-%m-%d", attrs={"type": "date"}
            ),
            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Detalhes, defeitos, onde comprou...",
                }
            ),
        }
        labels = {
            "name": "Nome do item",
            "category": "Categoria",
            "condition": "Condição",
            "acquired_on": "Data de aquisição",
            "notes": "Observações",
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["category"].queryset = Category.objects.filter(user=user)
        self.fields["category"].empty_label = "Sem categoria"
        self.fields["acquired_on"].input_formats = ["%Y-%m-%d", "%d/%m/%Y"]

    def clean(self):
        dados = super().clean()
        custo = dados.get("cost_cents")
        referencia = dados.get("reference_cents")
        if custo is not None and custo == 0:
            self.add_error("cost_cents", "O custo precisa ser maior que zero.")
        if custo and referencia and referencia < custo // 10:
            self.add_error(
                "reference_cents",
                "A referência está muito abaixo do custo. Confira os valores.",
            )
        return dados


class SaleForm(StyledFormMixin, forms.ModelForm):
    price_cents = BRLCentsField(label="Valor da venda")
    fees_cents = BRLCentsField(label="Taxas (comissão, frete)", required=False)

    class Meta:
        model = Sale
        fields = ["price_cents", "fees_cents", "channel", "sold_on"]
        widgets = {
            "sold_on": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        }
        labels = {
            "channel": "Onde vendeu",
            "sold_on": "Data da venda",
        }

    def __init__(self, *args, item=None, **kwargs):
        self.item = item
        super().__init__(*args, **kwargs)
        self.fields["sold_on"].input_formats = ["%Y-%m-%d", "%d/%m/%Y"]
        if item is not None:
            # Permite que o ModelForm valide as regras do Sale.clean (ex.: venda
            # antes da aquisição) antes de o item ser associado na view.
            self.instance.item = item
            preview_url = reverse("sale_preview", args=[item.pk])
            for nome in ("price_cents", "fees_cents"):
                self.fields[nome].widget.attrs.update(
                    {
                        "hx-post": preview_url,
                        "hx-trigger": "input changed delay:250ms",
                        "hx-target": "#sale-preview",
                        "hx-swap": "innerHTML",
                        "hx-include": "closest form",
                    }
                )
            if not self.is_bound:
                if item.reference_cents:
                    self.initial.setdefault("price_cents", item.reference_cents)
                self.initial.setdefault("fees_cents", 0)

    def clean_fees_cents(self):
        taxas = self.cleaned_data.get("fees_cents") or 0
        preco = self.cleaned_data.get("price_cents")
        if preco is not None and taxas > preco:
            raise ValidationError(
                "As taxas não podem ser maiores que o valor da venda."
            )
        return taxas


class CategoryForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "color"]
        widgets = {
            "name": forms.TextInput(
                attrs={"placeholder": "Ex.: Eletrodomésticos", "autofocus": True}
            ),
        }
        labels = {"name": "Nome da categoria", "color": "Cor"}
