/* BriqueStats — comportamento de UI (sem framework) */

(function () {
  "use strict";

  // ---------------------------------------------------------------------
  // Modal (<dialog>) controlado pelo HTMX
  // ---------------------------------------------------------------------
  function modalEl() {
    return document.getElementById("modal");
  }

  document.addEventListener("DOMContentLoaded", function () {
    var modal = modalEl();
    if (modal) {
      modal.addEventListener("close", function () {
        modal.innerHTML = "";
      });
      // Clique no backdrop fecha
      modal.addEventListener("click", function (event) {
        if (event.target === modal) modal.close();
      });
    }

    document.querySelectorAll("[data-toast]").forEach(function (el) {
      window.setTimeout(function () {
        el.classList.add("opacity-0", "translate-y-2");
        window.setTimeout(function () {
          el.remove();
        }, 300);
      }, 5200);
    });

    setupMarketPreview();
  });

  document.body.addEventListener("htmx:afterSwap", function (event) {
    var modal = modalEl();
    if (!modal) return;
    var alvo = event.detail.target;
    if ((alvo === modal || modal.contains(alvo)) && modal.innerHTML.trim()) {
      if (!modal.open) modal.showModal();
    }
  });

  document.body.addEventListener("htmx:responseError", function () {
    var modal = modalEl();
    if (modal && !modal.open) modal.showModal();
  });

  // ---------------------------------------------------------------------
  // Formulário de item: prévia "comprei X% abaixo do mercado"
  // ---------------------------------------------------------------------
  function parseBRL(raw) {
    if (!raw) return null;
    var texto = String(raw)
      .replace(/R\$/g, "")
      .replace(/\s|\u00a0/g, "")
      .trim();
    if (!texto) return null;
    var temVirgula = texto.indexOf(",") !== -1;
    var temPonto = texto.indexOf(".") !== -1;

    if (temVirgula && temPonto) {
      texto = texto.replace(/\./g, "").replace(",", ".");
    } else if (temVirgula) {
      texto = texto.replace(",", ".");
    } else if (temPonto) {
      var partes = texto.split(".");
      if (partes.length === 2 && partes[1].length === 3 && partes[0].length <= 3) {
        texto = partes.join("");
      } else if (partes.length > 2) {
        texto = partes.join("");
      }
    }
    var numero = parseFloat(texto);
    if (!isFinite(numero)) return null;
    return Math.round(numero * 100);
  }

  function brl(cents) {
    return (cents / 100).toLocaleString("pt-BR", {
      style: "currency",
      currency: "BRL",
    });
  }

  function setupMarketPreview() {
    var form = document.getElementById("item-form");
    if (!form) return;
    var custo = form.querySelector("[name='cost_cents']");
    var referencia = form.querySelector("[name='reference_cents']");
    var saida = document.getElementById("market-preview");
    if (!custo || !referencia || !saida) return;

    function atualizar() {
      var c = parseBRL(custo.value);
      var r = parseBRL(referencia.value);
      if (!c || !r) {
        saida.innerHTML =
          '<span class="text-slate-400">Preencha custo e referência para ver a comparação.</span>';
        return;
      }
      var diff = ((r - c) / r) * 100;
      var sinal = diff >= 0 ? "abaixo" : "acima";
      var cor = diff >= 0 ? "text-emerald-600" : "text-rose-600";
      var seta = diff >= 0 ? "↓" : "↑";
      saida.innerHTML =
        '<span class="' +
        cor +
        ' font-semibold tabular-nums">' +
        seta +
        " " +
        Math.abs(diff).toLocaleString("pt-BR", {
          minimumFractionDigits: 1,
          maximumFractionDigits: 1,
        }) +
        "%</span> " +
        '<span class="text-slate-600">' +
        sinal +
        " do preço de mercado</span>" +
        '<span class="mt-1 block text-xs text-slate-400">Economia de ' +
        brl(Math.max(r - c, 0)) +
        " em relação à referência.</span>";
    }

    custo.addEventListener("input", atualizar);
    referencia.addEventListener("input", atualizar);
    atualizar();
  }
})();
