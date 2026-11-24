from __future__ import annotations

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from config.ui import StyledFormMixin


class SignupForm(StyledFormMixin, UserCreationForm):
    email = forms.EmailField(
        label="E-mail",
        required=False,
        help_text="Opcional, mas ajuda a recuperar o acesso.",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")
        labels = {"username": "Nome de usuário"}
        widgets = {
            "username": forms.TextInput(
                attrs={"autofocus": True, "autocomplete": "username"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].label = "Senha"
        self.fields["password2"].label = "Confirme a senha"

    def save(self, commit: bool = True):
        usuario = super().save(commit=False)
        usuario.email = self.cleaned_data.get("email", "")
        if commit:
            usuario.save()
        return usuario
