from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("entrar/", views.BriqueLoginView.as_view(), name="login"),
    path("sair/", auth_views.LogoutView.as_view(), name="logout"),
    path("cadastrar/", views.SignupView.as_view(), name="signup"),
    path("demo/", views.demo_login, name="demo_login"),
]
