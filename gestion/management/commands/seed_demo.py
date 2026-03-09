from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.utils import timezone

from green_city.permissions import (
    ROLE_GESTIONNAIRE_GLOBAL,
    ROLE_GESTIONNAIRE_PARTICULIER,
    ROLE_MAIRE,
)
from gestion.models import (
    ArticleStock,
    Equipe,
    Equipement,
    EspaceVert,
    Intervention,
    Materiel,
    MouvementStock,
    Signalement,
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Genere un jeu de donnees de demonstration complet.'

    def handle(self, *args, **options):
        self._ensure_groups()
        users = self._seed_users()
        espaces = self._seed_espaces()
        equipe = self._seed_equipe(users)
        self._seed_equipements(espaces)
        self._seed_interventions(espaces, equipe, users['global'])
        self._seed_materiel()
        self._seed_stock(users['global'])
        self._seed_signalements(espaces, users['particulier'])
        self.stdout.write(self.style.SUCCESS('Donnees de demo creees avec succes.'))

    def _ensure_groups(self):
        for role in [ROLE_GESTIONNAIRE_PARTICULIER, ROLE_GESTIONNAIRE_GLOBAL, ROLE_MAIRE]:
            Group.objects.get_or_create(name=role)

    def _seed_users(self):
        users = {
            'particulier': self._create_user(
                username='agent1',
                password='ChangeMe123!',
                first_name='Ali',
                last_name='Agent',
                email='agent1@ville.local',
                role=ROLE_GESTIONNAIRE_PARTICULIER,
            ),
            'global': self._create_user(
                username='manager1',
                password='ChangeMe123!',
                first_name='Nora',
                last_name='Manager',
                email='manager1@ville.local',
                role=ROLE_GESTIONNAIRE_GLOBAL,
            ),
            'maire': self._create_user(
                username='maire1',
                password='ChangeMe123!',
                first_name='Jean',
                last_name='Maire',
                email='maire1@ville.local',
                role=ROLE_MAIRE,
            ),
        }
        return users

    def _create_user(self, username, password, first_name, last_name, email, role):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'is_active': True,
            },
        )
        if created:
            user.set_password(password)
            user.save()
        group = Group.objects.get(name=role)
        user.groups.add(group)
        if hasattr(user, 'profile'):
            user.profile.role_principal = role
            user.profile.save(update_fields=['role_principal'])
        return user

    def _seed_espaces(self):
        parc, _ = EspaceVert.objects.get_or_create(
            nom='Parc Central',
            defaults={
                'type_espace': EspaceVert.TypeEspace.PARC,
                'superficie_m2': Decimal('12500.00'),
                'adresse': 'Avenue des Acacias',
                'zone': 'Centre',
            },
        )
        stade, _ = EspaceVert.objects.get_or_create(
            nom='Stade Municipal Nord',
            defaults={
                'type_espace': EspaceVert.TypeEspace.STADE,
                'superficie_m2': Decimal('21000.00'),
                'adresse': 'Rue des Sports',
                'zone': 'Nord',
            },
        )
        return {'parc': parc, 'stade': stade}

    def _seed_equipements(self, espaces):
        Equipement.objects.get_or_create(
            espace=espaces['parc'],
            nom='Banc',
            defaults={'quantite': 12, 'etat': Equipement.Etat.BON, 'details': 'Bancs en bois'},
        )
        Equipement.objects.get_or_create(
            espace=espaces['parc'],
            nom='Balançoire',
            defaults={'quantite': 2, 'etat': Equipement.Etat.USE, 'details': 'Aire enfants'},
        )
        Equipement.objects.get_or_create(
            espace=espaces['stade'],
            nom='Projecteur',
            defaults={'quantite': 8, 'etat': Equipement.Etat.BON, 'details': 'Eclairage principal'},
        )

    def _seed_equipe(self, users):
        equipe, _ = Equipe.objects.get_or_create(nom='Equipe A', defaults={'zone_assignee': 'Centre'})
        equipe.agents.add(users['particulier'])
        return equipe

    def _seed_interventions(self, espaces, equipe, creator):
        now = timezone.now()
        Intervention.objects.get_or_create(
            type_intervention=Intervention.TypeIntervention.TONTE,
            espace=espaces['parc'],
            planifiee_le=now + timedelta(days=1),
            defaults={
                'equipe': equipe,
                'statut': Intervention.Statut.PREVUE,
                'cout': Decimal('150.00'),
                'cree_par': creator,
                'notes': 'Tonte hebdomadaire',
            },
        )
        Intervention.objects.get_or_create(
            type_intervention=Intervention.TypeIntervention.ARROSAGE,
            espace=espaces['parc'],
            planifiee_le=now + timedelta(days=2),
            defaults={
                'equipe': equipe,
                'statut': Intervention.Statut.PREVUE,
                'cout': Decimal('80.00'),
                'cree_par': creator,
            },
        )

    def _seed_materiel(self):
        Materiel.objects.get_or_create(
            nom='Tondeuse Pro X',
            categorie=Materiel.Categorie.TONDEUSE,
            defaults={
                'etat': Materiel.Etat.DISPONIBLE,
                'quantite_totale': 3,
                'quantite_disponible': 2,
            },
        )
        Materiel.objects.get_or_create(
            nom='Taille-haie Turbo',
            categorie=Materiel.Categorie.TAILLE_HAIE,
            defaults={
                'etat': Materiel.Etat.EN_REPARATION,
                'quantite_totale': 2,
                'quantite_disponible': 1,
            },
        )

    def _seed_stock(self, user):
        article, _ = ArticleStock.objects.get_or_create(
            nom='Fleurs saisonnieres',
            defaults={'unite': ArticleStock.Unite.UNITE, 'quantite': Decimal('300.00'), 'seuil_alerte': Decimal('80.00')},
        )
        MouvementStock.objects.get_or_create(
            article=article,
            type_mouvement=MouvementStock.TypeMouvement.SORTIE,
            quantite=Decimal('20.00'),
            motif='Plantation printemps',
            defaults={'cree_par': user},
        )

    def _seed_signalements(self, espaces, user):
        Signalement.objects.get_or_create(
            espace=espaces['parc'],
            description='Balançoire endommagee au parc principal',
            defaults={
                'priorite': Signalement.Priorite.HAUTE,
                'statut': Signalement.Statut.OUVERT,
                'cree_par': user,
            },
        )
