from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from inventory import selectors


def health(request):
    return JsonResponse({"status": "ok"})


@login_required
def dashboard(request):
    metricas = selectors.dashboard_metrics(request.user)
    mensal = selectors.monthly_profit(request.user)
    categorias = selectors.roi_by_category(request.user)

    dados_graficos = {
        "monthly": {
            "labels": [mes["label"] for mes in mensal],
            "profit": [round(mes["profit"] / 100, 2) for mes in mensal],
            "revenue": [round(mes["revenue"] / 100, 2) for mes in mensal],
            "count": [mes["count"] for mes in mensal],
        },
        "categories": {
            "labels": [linha["name"] for linha in categorias],
            "roi": [linha["roi_float"] for linha in categorias],
            "profit": [round(linha["profit"] / 100, 2) for linha in categorias],
        },
    }

    contexto = {
        "metrics": metricas,
        "categorias_roi": categorias,
        "chart_data": dados_graficos,
        "top_items": selectors.top_items_by_profit(request.user),
        "recent_items": selectors.recent_items(request.user),
        "recent_sales": selectors.recent_sales(request.user),
        "tem_dados": metricas.stock_count > 0 or metricas.sold_count > 0,
    }
    return render(request, "dashboard/dashboard.html", contexto)
