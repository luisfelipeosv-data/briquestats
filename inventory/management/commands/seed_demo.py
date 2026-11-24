from django.core.management.base import BaseCommand

from inventory.demo import (
    DEMO_PASSWORD,
    DEMO_USERNAME,
    ensure_demo_user,
    seed_demo_data,
)


class Command(BaseCommand):
    help = "Cria a conta demo com categorias, itens e vendas fictícias."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Apaga os dados da conta demo antes de recriar.",
        )

    def handle(self, *args, **options):
        usuario = ensure_demo_user()
        if options["reset"]:
            seed_demo_data(usuario, reset=True)

        total_itens = usuario.items.count()
        total_vendas = usuario.items.filter(status="vendido").count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Conta demo pronta: {total_itens} itens ({total_vendas} vendidos)."
            )
        )
        self.stdout.write(f"  usuário: {DEMO_USERNAME}")
        self.stdout.write(f"  senha:   {DEMO_PASSWORD}")
