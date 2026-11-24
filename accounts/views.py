from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView

from inventory.demo import ensure_demo_user

from .forms import SignupForm

BACKEND = "django.contrib.auth.backends.ModelBackend"


class BriqueLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


class SignupView(CreateView):
    form_class = SignupForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("dashboard")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        resposta = super().form_valid(form)
        login(self.request, self.object, backend=BACKEND)
        messages.success(
            self.request,
            f"Bem-vindo ao BriqueStats, {self.object.username}! Comece cadastrando seu primeiro item.",
        )
        return resposta


@require_POST
def demo_login(request):
    usuario = ensure_demo_user()
    login(request, usuario, backend=BACKEND)
    messages.info(
        request,
        "Você está na conta demo. Fique à vontade para criar, vender e desfazer — "
        "os dados são fictícios.",
    )
    return redirect("dashboard")
