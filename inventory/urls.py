from django.urls import path

from . import views

urlpatterns = [
    path("itens/", views.ItemListView.as_view(), name="item_list"),
    path("itens/novo/", views.ItemCreateView.as_view(), name="item_create"),
    path("itens/<int:pk>/", views.ItemDetailView.as_view(), name="item_detail"),
    path("itens/<int:pk>/editar/", views.ItemUpdateView.as_view(), name="item_update"),
    path("itens/<int:pk>/arquivar/", views.item_archive, name="item_archive"),
    path("itens/<int:pk>/desarquivar/", views.item_unarchive, name="item_unarchive"),
    path("itens/<int:pk>/remover/", views.item_delete, name="item_delete"),
    path("itens/<int:pk>/vender/", views.sale_create, name="sale_create"),
    path("itens/<int:pk>/preview-venda/", views.sale_preview, name="sale_preview"),
    path("vendas/", views.SaleListView.as_view(), name="sale_list"),
    path("vendas/<int:pk>/desfazer/", views.sale_delete, name="sale_delete"),
    path("categorias/", views.category_list, name="category_list"),
    path(
        "categorias/<int:pk>/editar/",
        views.category_update,
        name="category_update",
    ),
    path(
        "categorias/<int:pk>/excluir/",
        views.category_delete,
        name="category_delete",
    ),
]
