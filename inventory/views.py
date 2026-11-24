from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from . import selectors
from .forms import CategoryForm, ItemForm, SaleForm
from .models import Category, Item, Sale
from .money import cents_to_brl, parse_brl_to_cents
from .services import ratio_percent

ORDENS = {
    "recentes": ("-acquired_on", "-id"),
    "antigos": ("acquired_on", "id"),
    "parados": ("acquired_on", "id"),
    "nome": ("name",),
    "custo_maior": ("-cost_cents",),
    "custo_menor": ("cost_cents",),
}


def _preview_context(item: Item, preco: int, taxas: int) -> dict:
    lucro = preco - taxas - item.cost_cents
    return {
        "item": item,
        "preco_cents": preco,
        "taxas_cents": taxas,
        "lucro_cents": lucro,
        "roi": ratio_percent(lucro, item.cost_cents),
        "margem": ratio_percent(lucro, preco),
        "agio": (
            ratio_percent(preco - item.reference_cents, item.reference_cents)
            if item.reference_cents
            else None
        ),
        "valido": preco > 0,
    }


class ItemQuerysetMixin(LoginRequiredMixin):
    def get_queryset(self):
        return Item.objects.filter(user=self.request.user).select_related(
            "category", "sales"
        )


class ItemListView(ItemQuerysetMixin, ListView):
    model = Item
    template_name = "inventory/item_list.html"
    context_object_name = "items"
    paginate_by = 10

    def get_template_names(self):
        if getattr(self.request, "htmx", False):
            return ["inventory/partials/inventory_panel.html"]
        return [self.template_name]

    def get_queryset(self):
        qs = super().get_queryset()

        self.busca = self.request.GET.get("q", "").strip()
        self.status = self.request.GET.get("status", "")
        self.categoria = self.request.GET.get("categoria", "")
        self.ordem = self.request.GET.get("ordem", "recentes")

        if self.busca:
            qs = qs.filter(
                Q(name__icontains=self.busca) | Q(notes__icontains=self.busca)
            )
        if self.categoria.isdigit():
            qs = qs.filter(category_id=int(self.categoria))

        self.qs_sem_status = qs

        if self.status in Item.Status.values:
            qs = qs.filter(status=self.status)

        return qs.order_by(*ORDENS.get(self.ordem, ORDENS["recentes"]))

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contagens = self.qs_sem_status.aggregate(
            todos=Count("id"),
            estoque=Count("id", filter=Q(status=Item.Status.IN_STOCK)),
            vendido=Count("id", filter=Q(status=Item.Status.SOLD)),
            arquivado=Count("id", filter=Q(status=Item.Status.ARCHIVED)),
        )
        contexto.update(
            {
                "busca": self.busca,
                "status_atual": self.status,
                "categoria_atual": self.categoria,
                "ordem_atual": self.ordem,
                "categorias": Category.objects.filter(user=self.request.user),
                "contagens": contagens,
                "base_query": self._base_query(),
                "ordens": [
                    ("recentes", "Mais recentes"),
                    ("parados", "Há mais tempo parados"),
                    ("nome", "Nome (A-Z)"),
                    ("custo_maior", "Maior custo"),
                    ("custo_menor", "Menor custo"),
                ],
            }
        )
        return contexto

    def _base_query(self) -> str:
        params = self.request.GET.copy()
        params.pop("page", None)
        return params.urlencode()


class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    form_class = ItemForm
    template_name = "inventory/item_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["titulo"] = "Novo item"
        contexto["subtitulo"] = "Registre a compra para acompanhar o lucro na venda."
        return contexto

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Item adicionado ao inventário.")
        return super().form_valid(form)


class ItemUpdateView(ItemQuerysetMixin, UpdateView):
    model = Item
    form_class = ItemForm
    template_name = "inventory/item_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["titulo"] = "Editar item"
        contexto["subtitulo"] = (
            "Ajuste os dados da compra. A venda é registrada à parte."
        )
        return contexto

    def form_valid(self, form):
        messages.success(self.request, "Item atualizado.")
        return super().form_valid(form)


class ItemDetailView(ItemQuerysetMixin, DetailView):
    model = Item
    template_name = "inventory/item_detail.html"
    context_object_name = "item"


@login_required
@require_POST
def item_archive(request, pk: int):
    item = get_object_or_404(Item, pk=pk, user=request.user)
    if item.is_sold:
        messages.error(request, "Não é possível arquivar um item já vendido.")
    else:
        item.status = Item.Status.ARCHIVED
        item.save(update_fields=["status", "updated_at"])
        messages.success(request, "Item arquivado.")
    return redirect(item)


@login_required
@require_POST
def item_unarchive(request, pk: int):
    item = get_object_or_404(Item, pk=pk, user=request.user)
    if item.status == Item.Status.ARCHIVED:
        item.status = Item.Status.IN_STOCK
        item.save(update_fields=["status", "updated_at"])
        messages.success(request, "Item voltou para o estoque.")
    return redirect(item)


@login_required
@require_POST
def item_delete(request, pk: int):
    item = get_object_or_404(Item, pk=pk, user=request.user)
    if item.is_sold:
        messages.error(request, "Desfaça a venda antes de remover um item vendido.")
        return redirect(item)
    nome = item.name
    item.delete()
    messages.success(request, f"“{nome}” foi removido do inventário.")
    return redirect("item_list")


# ---------------------------------------------------------------------------
# Vendas
# ---------------------------------------------------------------------------
@login_required
def sale_create(request, pk: int):
    item = get_object_or_404(
        Item.objects.select_related("category"), pk=pk, user=request.user
    )

    if item.sale is not None:
        messages.info(request, "Este item já foi vendido.")
        return redirect(item)

    if request.method == "POST":
        form = SaleForm(request.POST, item=item)
        preco = parse_brl_to_cents(request.POST.get("price_cents")) or 0
        taxas = parse_brl_to_cents(request.POST.get("fees_cents")) or 0

        if form.is_valid():
            sale = form.save(commit=False)
            sale.item = item
            sale.save()
            messages.success(
                request,
                f"Venda registrada: lucro de {cents_to_brl(sale.profit_cents)}.",
            )
            if getattr(request, "htmx", False):
                resposta = HttpResponse(status=200)
                resposta["HX-Redirect"] = reverse("item_detail", args=[item.pk])
                return resposta
            return redirect(item)
    else:
        form = SaleForm(item=item, initial={"sold_on": timezone.localdate()})
        preco = item.reference_cents or 0
        taxas = 0

    contexto = {"item": item, "form": form}
    contexto.update(_preview_context(item, preco, taxas))

    if getattr(request, "htmx", False):
        return render(request, "inventory/partials/sale_modal.html", contexto)
    return render(request, "inventory/sale_form.html", contexto)


@login_required
@require_POST
def sale_preview(request, pk: int):
    item = get_object_or_404(Item, pk=pk, user=request.user)
    preco = parse_brl_to_cents(request.POST.get("price_cents")) or 0
    taxas = parse_brl_to_cents(request.POST.get("fees_cents")) or 0
    return render(
        request,
        "inventory/partials/sale_preview.html",
        _preview_context(item, preco, taxas),
    )


class SaleListView(LoginRequiredMixin, ListView):
    model = Sale
    template_name = "inventory/sale_list.html"
    context_object_name = "sales"
    paginate_by = 15

    def get_queryset(self):
        return (
            Sale.objects.filter(item__user=self.request.user)
            .select_related("item", "item__category")
            .order_by("-sold_on", "-id")
        )

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["resumo"] = selectors.dashboard_metrics(self.request.user)
        return contexto


@login_required
@require_POST
def sale_delete(request, pk: int):
    sale = get_object_or_404(Sale, pk=pk, item__user=request.user)
    item = sale.item
    sale.delete()
    messages.success(
        request, f"Venda de “{item.name}” desfeita. O item voltou ao estoque."
    )
    return redirect(item)


# ---------------------------------------------------------------------------
# Categorias
# ---------------------------------------------------------------------------
@login_required
def category_list(request):
    form = CategoryForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        categoria = form.save(commit=False)
        categoria.user = request.user
        categoria.save()
        messages.success(request, f"Categoria “{categoria.name}” criada.")
        return redirect("category_list")

    categorias = (
        Category.objects.filter(user=request.user)
        .annotate(
            total=Count("items"),
            em_estoque=Count("items", filter=Q(items__status=Item.Status.IN_STOCK)),
        )
        .order_by("name")
    )

    contexto = {
        "form": form,
        "categorias": categorias,
        "resumo": selectors.dashboard_metrics(request.user),
    }
    return render(request, "inventory/category_list.html", contexto)


@login_required
def category_update(request, pk: int):
    categoria = get_object_or_404(Category, pk=pk, user=request.user)
    form = CategoryForm(request.POST or None, instance=categoria)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Categoria atualizada.")
        if getattr(request, "htmx", False):
            resposta = HttpResponse(status=200)
            resposta["HX-Redirect"] = reverse("category_list")
            return resposta
        return redirect("category_list")

    contexto = {"categoria": categoria, "form": form}
    if getattr(request, "htmx", False):
        return render(request, "inventory/partials/category_modal.html", contexto)
    return render(request, "inventory/category_form.html", contexto)


@login_required
@require_POST
def category_delete(request, pk: int):
    categoria = get_object_or_404(Category, pk=pk, user=request.user)
    nome = categoria.name
    categoria.delete()  # itens ficam sem categoria (SET_NULL)
    messages.success(request, f"Categoria “{nome}” removida.")
    return redirect("category_list")
