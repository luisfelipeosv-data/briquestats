# BriqueStats

> Controle financeiro para quem compra para revender.

O BriqueStats é um sistema de gestão de inventário e lucratividade para revendedores.
Em vez de olhar só para o saldo da conta, ele responde às perguntas que importam para
quem vive de comprar e vender peças:

- Quanto de capital está **parado no estoque**?
- Qual **categoria** realmente dá lucro?
- Quanto tempo cada peça leva para **girar**?
- Comprei barato em relação ao mercado? Vendi bem?

> **Screenshot / GIF:** adicione aqui um GIF de 20s mostrando o dashboard e o registro
> de uma venda. É a primeira coisa que um recrutador olha.

---

## O problema

Planilhas de revenda viram um labirinto de colunas: custo, preço de mercado, taxas,
data de compra, data de venda, lucro, margem. O cálculo é sempre o mesmo e sempre
sujeito a erro. O BriqueStats centraliza o inventário e calcula tudo por item —
inclusive o que a maioria dos apps de finanças ignora: **tempo de giro** e
**ROI ponderado por categoria**.

## Funcionalidades

- **Inventário** com busca, filtros por status/categoria e ordenação
- **Categorias personalizadas** (Eletrodomésticos, PC, Automotivo...) com cor
- **Cadastro de item** com custo, preço de referência de mercado e data de aquisição
- **Registro de venda** em modal, com lucro, ROI e margem calculados **ao vivo**
- **Desfazer venda** devolvendo o item ao estoque
- **Dashboard** com capital em estoque, lucro realizado, ROI médio, giro médio e
  gráficos de lucro por mês e ROI por categoria
- **Multi-usuário** com isolamento total de dados
- **Conta demo** com 15 itens e 5 vendas para explorar sem cadastrar nada
- Responsivo, com estados de vazio, erro e carregamento

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Django 6 (Python 3.12+) |
| Interatividade | HTMX 2 |
| Estilo | Tailwind CSS 4 (CLI standalone, sem Node) |
| Banco (dev) | SQLite |
| Banco (prod) | PostgreSQL |
| Gráficos | Chart.js 4 |
| Testes | pytest + pytest-django |
| Lint | ruff |
| Deploy | Railway |

---

## Decisões de engenharia

### 1. Dinheiro em centavos, nunca em float

`R$ 1.199,90` é armazenado como `119990` (`PositiveIntegerField`). Somar floats de
dinheiro acumula erro; inteiros não. A conversão de/para o formato brasileiro fica
isolada em `inventory/money.py` e é coberta por testes com `1.199,90`, `1199.90`,
`1.234.567,89` e entradas inválidas.

### 2. Dado derivado é calculado, não digitado

O usuário **não** digita "quanto a mais em % vendi". Ele informa o valor da venda e o
sistema mostra ROI, margem e ágio vs. mercado em tempo real — no servidor
(`inventory/services.py`) e no cliente, para feedback imediato. Uma única fonte de
verdade para a regra de negócio.

### 3. ROI médio é ponderado por custo

A média de ROIs mente: um item de R$ 50 com 200% de retorno não pode pesar o mesmo que
um de R$ 5.000 com 20%. O dashboard usa `soma(lucro) / soma(custo)`, que reflete o
retorno real sobre o capital investido.

### 4. Isolamento de dados no ORM — e testado

Todo queryset é filtrado por `request.user`. Não existe "confiar na URL": acessar o
item de outro usuário retorna 404, e há testes cobrindo listagem, detalhe, edição e
venda. Segurança de multi-tenant tratada como requisito, não como detalhe.

### 5. HTMX em vez de SPA

O app é renderizado no servidor. HTMX cuida dos trechos interativos (filtros, modal de
venda, preview de cálculo) sem estado duplicado no cliente, sem bundler e sem uma API
separada. Menos superfície, mais entrega.

---

## Rodando localmente

Requisitos: Python 3.12+ e `curl`. **Não é necessário Node.**

```bash
git clone <url-do-repo>
cd briquestats

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# Tailwind standalone (uma vez)
mkdir -p bin
curl -sSL -o bin/tailwindcss \
  https://github.com/tailwindlabs/tailwindcss/releases/download/v4.3.5/tailwindcss-linux-x64
chmod +x bin/tailwindcss

# CSS
./bin/tailwindcss -i theme/input.css -o static/css/app.css --minify

cp .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Abra <http://localhost:8000>.

> O CSS compilado (`static/css/app.css`) é versionado para simplificar o deploy.
> Ao alterar templates ou classes, rode o comando do Tailwind novamente — ou
> `./bin/tailwindcss -i theme/input.css -o static/css/app.css --watch` enquanto
> desenvolve.

### Conta demo

Clique em **“Explorar com a conta demo”** na tela de login, ou use:

```
usuário: demo
senha:   briquestats
```

Para recriar os dados: `python manage.py seed_demo --reset`.

## Testes e qualidade

```bash
pytest          # 65 testes
ruff check .    # lint
python manage.py check
```

A suíte cobre:

- conversão de moeda brasileira (ida e volta)
- lucro, ROI, margem, ágio e giro — inclusive custo zero e prejuízo
- agregações do dashboard e séries de gráfico
- fluxo de cadastro → venda → desfazer venda
- isolamento entre usuários (404 e listagem filtrada)
- validações de formulário (taxas > venda, venda antes da compra)

## Deploy (Railway)

1. Crie um projeto no Railway e adicione o plugin **PostgreSQL**.
2. Conecte o repositório do GitHub.
3. Configure as variáveis de ambiente:

   | Variável | Valor |
   |---|---|
   | `SECRET_KEY` | uma chave aleatória longa |
   | `DEBUG` | `False` |
   | `ALLOWED_HOSTS` | `seu-app.up.railway.app` |
   | `CSRF_TRUSTED_ORIGINS` | `https://seu-app.up.railway.app` |
   | `DATABASE_URL` | referência ao plugin Postgres |
   | `SECURE_SSL_REDIRECT` | `True` |

4. O `railway.json` já roda `collectstatic` no build e `migrate` no start.
5. Depois do primeiro deploy, crie a conta demo:

   ```bash
   python manage.py seed_demo
   ```

> `DEBUG` precisa estar `False` **no build** para o WhiteNoise gerar o manifesto
> dos arquivos estáticos.

## Estrutura

```
briquestats/
├── config/                 # settings, urls, views de erro
├── accounts/               # login, cadastro, conta demo
├── inventory/
│   ├── models.py           # Category, Item, Sale
│   ├── money.py            # parsing/formatação de BRL em centavos
│   ├── services.py         # cálculos puros (testáveis sem banco)
│   ├── selectors.py        # agregações e séries dos gráficos
│   ├── forms.py            # BRLCentsField + formulários
│   ├── views.py            # CRUD, venda, HTMX
│   ├── demo.py             # dados fictícios da conta demo
│   └── tests/
├── dashboard/              # painel e gráficos
├── templates/              # base, parciais HTMX, erros
├── static/                 # css compilado, js, vendor
├── theme/input.css         # fonte do Tailwind
└── bin/tailwindcss         # binário standalone (não versionado)
```

## Roadmap

Veja [ROADMAP.md](ROADMAP.md). Resumo: fotos dos itens, importação de planilha,
integração com Mercado Livre/OLX, venda em lote, exportação CSV e alertas de item
parado.

## Contexto

Este é meu primeiro projeto de portfólio. A escolha de Django + HTMX foi deliberada:
priorizar um produto completo, com autenticação, regras de negócio testadas e deploy
real, em vez de aprender três frameworks ao mesmo tempo. O foco foi entregar software
que funciona e cujo código eu consigo explicar linha por linha.

## Licença

MIT — veja [LICENSE](LICENSE).
