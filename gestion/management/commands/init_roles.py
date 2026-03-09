from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from green_city.permissions import (
    AVAILABLE_ROLES,
)


class Command(BaseCommand):
    help = 'Cree les groupes de roles metiers necessaires.'

    def handle(self, *args, **options):
        for role in AVAILABLE_ROLES:
            Group.objects.get_or_create(name=role)
        self.stdout.write(self.style.SUCCESS('Groupes crees/confirmes avec succes.'))
