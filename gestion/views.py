from datetime import date, datetime

from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from green_city.permissions import (
    ROLE_GESTIONNAIRE_GLOBAL,
    ROLE_GESTIONNAIRE_PARTICULIER,
    ROLE_MAIRE,
    has_any_role,
    has_role,
)
from .models import (
    ActiviteLog,
    ArticleStock,
    Equipe,
    Equipement,
    EspaceVert,
    Intervention,
    Materiel,
    MouvementStock,
    Notification,
    Signalement,
)
from .serializers import (
    ActiviteLogSerializer,
    ArticleStockSerializer,
    ChangerStatutSignalementSerializer,
    EquipeSerializer,
    EquipementSerializer,
    EspaceVertSerializer,
    InterventionSerializer,
    MarquerInterventionEffectueeSerializer,
    MaterielSerializer,
    MouvementStockSerializer,
    NotificationSerializer,
    SignalementSerializer,
)

User = get_user_model()

READ_ACTIONS = {'list', 'retrieve'}


def journaliser_action(user, action, instance=None, details=''):
    ActiviteLog.objects.create(
        utilisateur=user,
        action=action,
        objet_type=instance.__class__.__name__ if instance else 'Systeme',
        objet_id=instance.pk if instance else None,
        details=details,
    )


def users_with_roles(roles: set[str]):
    return User.objects.filter(groups__name__in=roles, is_active=True).distinct()


def notifier_roles(roles: set[str], type_notification, titre, message, url_cible=''):
    recipients = users_with_roles(roles)
    notifications = [
        Notification(
            destinataire=user,
            type_notification=type_notification,
            titre=titre,
            message=message,
            url_cible=url_cible,
        )
        for user in recipients
    ]
    if notifications:
        Notification.objects.bulk_create(notifications)


class RoleActionPermissionMixin:
    permission_classes = [permissions.IsAuthenticated]
    read_roles = {ROLE_GESTIONNAIRE_PARTICULIER, ROLE_GESTIONNAIRE_GLOBAL, ROLE_MAIRE}
    write_roles = {ROLE_GESTIONNAIRE_GLOBAL}
    action_roles = {}

    def has_role_access(self, roles):
        return has_any_role(self.request.user, roles)

    def check_action_permission(self):
        if self.action in self.action_roles:
            return self.has_role_access(self.action_roles[self.action])
        if self.action in READ_ACTIONS:
            return self.has_role_access(self.read_roles)
        return self.has_role_access(self.write_roles)

    def get_permissions(self):
        perms = super().get_permissions()
        if not self.check_action_permission():
            self.permission_denied(self.request, message='Action non autorisee pour votre role.')
        return perms


class EspaceVertViewSet(RoleActionPermissionMixin, viewsets.ModelViewSet):
    queryset = EspaceVert.objects.all().order_by('nom')
    serializer_class = EspaceVertSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        journaliser_action(self.request.user, 'Creation espace vert', instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        journaliser_action(self.request.user, 'Mise a jour espace vert', instance)

    def perform_destroy(self, instance):
        journaliser_action(self.request.user, 'Suppression espace vert', instance)
        super().perform_destroy(instance)


class EquipementViewSet(RoleActionPermissionMixin, viewsets.ModelViewSet):
    queryset = Equipement.objects.select_related('espace').all().order_by('nom')
    serializer_class = EquipementSerializer
    action_roles = {
        'partial_update': {ROLE_GESTIONNAIRE_PARTICULIER, ROLE_GESTIONNAIRE_GLOBAL},
    }

    def perform_create(self, serializer):
        instance = serializer.save()
        journaliser_action(self.request.user, 'Creation equipement', instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        journaliser_action(self.request.user, 'Notification etat equipement', instance)


class EquipeViewSet(RoleActionPermissionMixin, viewsets.ModelViewSet):
    queryset = Equipe.objects.prefetch_related('agents').all().order_by('nom')
    serializer_class = EquipeSerializer
    read_roles = {ROLE_GESTIONNAIRE_GLOBAL, ROLE_MAIRE}

    def perform_create(self, serializer):
        instance = serializer.save()
        journaliser_action(self.request.user, 'Creation equipe', instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        journaliser_action(self.request.user, 'Mise a jour equipe', instance)


class InterventionViewSet(RoleActionPermissionMixin, viewsets.ModelViewSet):
    queryset = Intervention.objects.select_related('espace', 'equipe', 'cree_par').all().order_by('-planifiee_le')
    serializer_class = InterventionSerializer
    action_roles = {
        'marquer_effectuee': {ROLE_GESTIONNAIRE_PARTICULIER, ROLE_GESTIONNAIRE_GLOBAL},
    }

    def get_queryset(self):
        qs = super().get_queryset()
        statut = self.request.query_params.get('statut')
        from_date = self.request.query_params.get('from')
        to_date = self.request.query_params.get('to')

        if has_role(self.request.user, ROLE_GESTIONNAIRE_PARTICULIER) and not has_any_role(
            self.request.user, {ROLE_GESTIONNAIRE_GLOBAL, ROLE_MAIRE}
        ):
            qs = qs.filter(equipe__agents=self.request.user).distinct()

        if statut:
            qs = qs.filter(statut=statut)
        if from_date:
            qs = qs.filter(planifiee_le__date__gte=self._parse_date(from_date))
        if to_date:
            qs = qs.filter(planifiee_le__date__lte=self._parse_date(to_date))
        return qs

    def perform_create(self, serializer):
        instance = serializer.save(cree_par=self.request.user)
        journaliser_action(self.request.user, 'Programmation intervention', instance)
        notifier_roles(
            {ROLE_GESTIONNAIRE_PARTICULIER},
            Notification.TypeNotification.INTERVENTION,
            'Nouvelle intervention planifiee',
            f'Intervention {instance.get_type_intervention_display()} sur {instance.espace.nom}',
            url_cible=f'/interventions/{instance.pk}',
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        journaliser_action(self.request.user, 'Mise a jour intervention', instance)

    @action(detail=True, methods=['post'], url_path='marquer-effectuee')
    def marquer_effectuee(self, request, pk=None):
        intervention = self.get_object()
        serializer = MarquerInterventionEffectueeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        intervention.statut = Intervention.Statut.TERMINEE
        intervention.terminee_le = timezone.now()
        notes = serializer.validated_data.get('notes')
        if notes:
            intervention.notes = notes
            intervention.save(update_fields=['statut', 'terminee_le', 'notes'])
        else:
            intervention.save(update_fields=['statut', 'terminee_le'])

        journaliser_action(request.user, 'Intervention marquee terminee', intervention)
        notifier_roles(
            {ROLE_GESTIONNAIRE_GLOBAL, ROLE_MAIRE},
            Notification.TypeNotification.INTERVENTION,
            'Intervention terminee',
            f'{intervention.get_type_intervention_display()} terminee sur {intervention.espace.nom}',
            url_cible=f'/interventions/{intervention.pk}',
        )
        return Response(InterventionSerializer(intervention).data, status=status.HTTP_200_OK)

    @staticmethod
    def _parse_date(value: str) -> date:
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError as exc:
            raise ValidationError(f'Date invalide: {value}. Format attendu: YYYY-MM-DD') from exc


class SignalementViewSet(RoleActionPermissionMixin, viewsets.ModelViewSet):
    queryset = Signalement.objects.select_related('espace', 'equipement', 'cree_par', 'assigne_a').all()
    serializer_class = SignalementSerializer
    action_roles = {
        'create': {ROLE_GESTIONNAIRE_PARTICULIER, ROLE_GESTIONNAIRE_GLOBAL},
        'changer_statut': {ROLE_GESTIONNAIRE_GLOBAL},
    }

    def get_queryset(self):
        qs = super().get_queryset()
        if has_role(self.request.user, ROLE_GESTIONNAIRE_PARTICULIER) and not has_any_role(
            self.request.user, {ROLE_GESTIONNAIRE_GLOBAL, ROLE_MAIRE}
        ):
            return qs.filter(cree_par=self.request.user)
        return qs

    def perform_create(self, serializer):
        instance = serializer.save(cree_par=self.request.user)
        journaliser_action(self.request.user, 'Signalement anomalie', instance)
        notifier_roles(
            {ROLE_GESTIONNAIRE_GLOBAL},
            Notification.TypeNotification.SIGNALEMENT,
            'Nouveau signalement',
            f'{instance.espace.nom}: {instance.description[:80]}',
            url_cible=f'/signalements/{instance.pk}',
        )

    @action(detail=True, methods=['post'], url_path='changer-statut')
    def changer_statut(self, request, pk=None):
        signalement = self.get_object()
        serializer = ChangerStatutSignalementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        signalement.statut = serializer.validated_data['statut']
        update_fields = ['statut']
        if signalement.statut == Signalement.Statut.RESOLU:
            signalement.resolved_at = timezone.now()
            update_fields.append('resolved_at')
        signalement.save(update_fields=update_fields)

        journaliser_action(request.user, 'Mise a jour statut signalement', signalement)
        if signalement.cree_par:
            Notification.objects.create(
                destinataire=signalement.cree_par,
                type_notification=Notification.TypeNotification.SIGNALEMENT,
                titre='Mise a jour de votre signalement',
                message=(
                    f'Signalement #{signalement.pk} passe en '
                    f'{signalement.get_statut_display().lower()}.'
                ),
                url_cible=f'/signalements/{signalement.pk}',
            )
        return Response(SignalementSerializer(signalement).data, status=status.HTTP_200_OK)


class MaterielViewSet(RoleActionPermissionMixin, viewsets.ModelViewSet):
    queryset = Materiel.objects.all().order_by('nom')
    serializer_class = MaterielSerializer
    read_roles = {ROLE_GESTIONNAIRE_GLOBAL, ROLE_MAIRE}

    def perform_create(self, serializer):
        instance = serializer.save()
        journaliser_action(self.request.user, 'Ajout materiel', instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        journaliser_action(self.request.user, 'Reparation/Mise a jour materiel', instance)


class ArticleStockViewSet(RoleActionPermissionMixin, viewsets.ModelViewSet):
    queryset = ArticleStock.objects.all().order_by('nom')
    serializer_class = ArticleStockSerializer
    read_roles = {ROLE_GESTIONNAIRE_GLOBAL, ROLE_MAIRE}


class MouvementStockViewSet(RoleActionPermissionMixin, viewsets.ModelViewSet):
    queryset = MouvementStock.objects.select_related('article', 'cree_par').all().order_by('-date_mouvement')
    serializer_class = MouvementStockSerializer
    read_roles = {ROLE_GESTIONNAIRE_GLOBAL, ROLE_MAIRE}

    def perform_create(self, serializer):
        instance = serializer.save(cree_par=self.request.user)
        journaliser_action(self.request.user, 'Mouvement stock', instance)
        if (
            instance.article.quantite <= instance.article.seuil_alerte
            and instance.type_mouvement == MouvementStock.TypeMouvement.SORTIE
        ):
            notifier_roles(
                {ROLE_GESTIONNAIRE_GLOBAL},
                Notification.TypeNotification.STOCK,
                'Alerte stock bas',
                f'{instance.article.nom} est passe sous le seuil d alerte.',
                url_cible=f'/articles-stock/{instance.article.pk}',
            )


class ActiviteLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ActiviteLog.objects.select_related('utilisateur').all()
    serializer_class = ActiviteLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        perms = super().get_permissions()
        allowed = has_any_role(self.request.user, {ROLE_GESTIONNAIRE_GLOBAL, ROLE_MAIRE})
        if not allowed:
            self.permission_denied(self.request, message='Action non autorisee pour votre role.')
        return perms

    def get_queryset(self):
        qs = super().get_queryset()
        from_date = self.request.query_params.get('from')
        to_date = self.request.query_params.get('to')
        if from_date:
            qs = qs.filter(created_at__date__gte=self._parse_date(from_date))
        if to_date:
            qs = qs.filter(created_at__date__lte=self._parse_date(to_date))
        return qs

    @staticmethod
    def _parse_date(value: str) -> date:
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError as exc:
            raise ValidationError(f'Date invalide: {value}. Format attendu: YYYY-MM-DD') from exc


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.select_related('destinataire').all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        return super().get_queryset().filter(destinataire=self.request.user)

    @action(detail=True, methods=['post'], url_path='marquer-lue')
    def marquer_lue(self, request, pk=None):
        notification = self.get_object()
        notification.lu = True
        notification.save(update_fields=['lu'])
        return Response(NotificationSerializer(notification).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='marquer-toutes-lues')
    def marquer_toutes_lues(self, request):
        updated = self.get_queryset().filter(lu=False).update(lu=True)
        return Response({'notifications_mises_a_jour': updated}, status=status.HTTP_200_OK)


class StatistiquesAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not has_any_role(request.user, {ROLE_GESTIONNAIRE_GLOBAL, ROLE_MAIRE}):
            self.permission_denied(request, message='Action non autorisee pour votre role.')

        start = request.query_params.get('start')
        end = request.query_params.get('end')

        interventions = Intervention.objects.all()
        mouvements = MouvementStock.objects.all()
        signalements = Signalement.objects.all()
        activites = ActiviteLog.objects.all()

        if start:
            start_date = self._parse_date(start)
            interventions = interventions.filter(planifiee_le__date__gte=start_date)
            mouvements = mouvements.filter(date_mouvement__date__gte=start_date)
            signalements = signalements.filter(created_at__date__gte=start_date)
            activites = activites.filter(created_at__date__gte=start_date)

        if end:
            end_date = self._parse_date(end)
            interventions = interventions.filter(planifiee_le__date__lte=end_date)
            mouvements = mouvements.filter(date_mouvement__date__lte=end_date)
            signalements = signalements.filter(created_at__date__lte=end_date)
            activites = activites.filter(created_at__date__lte=end_date)

        interventions_par_mois = list(
            interventions.annotate(mois=TruncMonth('planifiee_le'))
            .values('mois')
            .annotate(nombre=Count('id'), depenses=Sum('cout'))
            .order_by('mois')
        )

        interventions_par_type = list(
            interventions.values('type_intervention').annotate(nombre=Count('id')).order_by('type_intervention')
        )

        consommation_stock = list(
            mouvements.filter(type_mouvement=MouvementStock.TypeMouvement.SORTIE)
            .annotate(mois=TruncMonth('date_mouvement'))
            .values('mois', 'article__nom')
            .annotate(quantite=Sum('quantite'))
            .order_by('mois', 'article__nom')
        )

        total_signalements = signalements.count()
        resolus = signalements.filter(statut=Signalement.Statut.RESOLU).count()
        taux_resolution = (resolus / total_signalements * 100) if total_signalements else 0

        activite_globale = list(
            activites.annotate(mois=TruncMonth('created_at'))
            .values('mois')
            .annotate(total=Count('id'))
            .order_by('mois')
        )

        return Response(
            {
                'interventions_par_mois': interventions_par_mois,
                'interventions_par_type': interventions_par_type,
                'consommation_stock_par_mois': consommation_stock,
                'signalements': {
                    'total': total_signalements,
                    'resolus': resolus,
                    'taux_resolution': round(taux_resolution, 2),
                },
                'activite_globale': activite_globale,
            }
        )

    @staticmethod
    def _parse_date(value: str) -> date:
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError as exc:
            raise ValidationError(f'Date invalide: {value}. Format attendu: YYYY-MM-DD') from exc
