"""Pequenos utilitários de UI compartilhados entre apps."""

from __future__ import annotations

from django import forms

BASE_INPUT = (
    "w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm "
    "text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400 "
    "focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
)
BASE_SELECT = BASE_INPUT + " select-chevron cursor-pointer pr-9 appearance-none"
BASE_TEXTAREA = BASE_INPUT + " min-h-24 resize-y"
BASE_CHECKBOX = (
    "h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-2 focus:ring-indigo-300"
)


class StyledFormMixin:
    """Aplica as classes do design system em todos os widgets do form."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                classes = BASE_CHECKBOX
            elif isinstance(widget, forms.Select):
                classes = BASE_SELECT
            elif isinstance(widget, forms.Textarea):
                classes = BASE_TEXTAREA
            else:
                classes = BASE_INPUT
            atual = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{classes} {atual}".strip()
