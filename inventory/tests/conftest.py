from datetime import date

import pytest
from django.contrib.auth.models import User

from inventory.models import Category, Item


@pytest.fixture
def usuario(db):
    return User.objects.create_user(username="ana", password="senha-forte-123")


@pytest.fixture
def outro_usuario(db):
    return User.objects.create_user(username="bruno", password="senha-forte-123")


@pytest.fixture
def cliente(client, usuario):
    client.force_login(usuario)
    return client


@pytest.fixture
def categoria(usuario):
    return Category.objects.create(user=usuario, name="PC & Hardware", color="violeta")


@pytest.fixture
def item(usuario, categoria):
    return Item.objects.create(
        user=usuario,
        category=categoria,
        name="SSD 1TB Kingston",
        cost_cents=28000,
        reference_cents=45000,
        acquired_on=date(2026, 1, 1),
    )
