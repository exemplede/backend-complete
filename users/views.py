from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.models import Group
from rest_framework import permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action

from green_city.permissions import (
    AVAILABLE_ROLES,
    ROLE_GESTIONNAIRE_GLOBAL,
    ROLE_MAIRE,
    has_any_role,
)
from gestion.models import ActiviteLog
from .serializers import (
    MeUpdateSerializer,
    PasswordChangeSerializer,
    RoleAssignmentSerializer,
    UserCreateSerializer,
    UserReadSerializer,
    UserUpdateSerializer,
)

User = get_user_model()


def log_user_action(user, action, target=None, details=''):
    ActiviteLog.objects.create(
        utilisateur=user,
        action=action,
        objet_type=target.__class__.__name__ if target else 'User',
        objet_id=target.pk if target else None,
        details=details,
    )


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'detail': 'Nom d\'utilisateur et mot de passe requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)

        if user is None:
            return Response(
                {'detail': 'Identifiants invalides.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {'detail': 'Compte désactivé.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Créer ou récupérer le token
        token, created = Token.objects.get_or_create(user=user)

        # Récupérer les groupes de l'utilisateur
        groups = list(user.groups.values_list('name', flat=True))

        return Response({
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'groups': groups,
            }
        }, status=status.HTTP_200_OK)


class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Supprimer le token de l'utilisateur
        request.user.auth_token.delete()
        return Response({'detail': 'Déconnexion réussie.'}, status=status.HTTP_200_OK)


class MeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserReadSerializer(request.user).data)

    def patch(self, request):
        serializer = MeUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(request.user, serializer.validated_data)
        log_user_action(request.user, 'Mise a jour profil personnel', request.user)
        return Response(UserReadSerializer(request.user).data)


class MePasswordAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ancien = serializer.validated_data['ancien_mot_de_passe']
        nouveau = serializer.validated_data['nouveau_mot_de_passe']

        if not request.user.check_password(ancien):
            return Response(
                {'detail': 'Ancien mot de passe incorrect.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.set_password(nouveau)
        request.user.save(update_fields=['password'])
        log_user_action(request.user, 'Changement mot de passe', request.user)
        return Response({'detail': 'Mot de passe mis a jour.'}, status=status.HTTP_200_OK)


class RoleListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not has_any_role(request.user, {ROLE_GESTIONNAIRE_GLOBAL, ROLE_MAIRE}):
            self.permission_denied(request, message='Action non autorisee pour votre role.')

        return Response(
            {
                'roles': AVAILABLE_ROLES,
                'description': {
                    'GestionnaireParticulier': 'Execute les operations quotidiennes',
                    'GestionnaireGlobal': 'Administre les ressources et la planification',
                    'Maire': 'Consulte les statistiques et l activite globale',
                },
            }
        )


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.select_related('profile').prefetch_related('groups').all().order_by('username')
    permission_classes = [permissions.IsAuthenticated]

    def _is_global_or_mayor(self):
        return has_any_role(self.request.user, {ROLE_GESTIONNAIRE_GLOBAL, ROLE_MAIRE})

    def _is_global(self):
        return has_any_role(self.request.user, {ROLE_GESTIONNAIRE_GLOBAL})

    def get_permissions(self):
        perms = super().get_permissions()
        if self.action in {'list', 'retrieve'}:
            allowed = self._is_global_or_mayor()
        else:
            allowed = self._is_global()

        if not allowed:
            self.permission_denied(self.request, message='Action non autorisee pour votre role.')
        return perms

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in {'update', 'partial_update'}:
            return UserUpdateSerializer
        return UserReadSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        log_user_action(self.request.user, 'Creation utilisateur', user)

    def perform_update(self, serializer):
        user = serializer.save()
        log_user_action(self.request.user, 'Mise a jour utilisateur', user)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if user == request.user:
            return Response(
                {'detail': 'Vous ne pouvez pas desactiver votre propre compte.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.is_active = False
        user.save(update_fields=['is_active'])
        log_user_action(request.user, 'Desactivation utilisateur', user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='set-roles')
    def set_roles(self, request, pk=None):
        user = self.get_object()
        serializer = RoleAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        roles = serializer.validated_data['roles']

        groups = Group.objects.filter(name__in=roles)
        user.groups.set(groups)
        if hasattr(user, 'profile'):
            user.profile.role_principal = roles[0]
            user.profile.save(update_fields=['role_principal'])

        log_user_action(
            request.user,
            'Attribution roles utilisateur',
            user,
            details=f'Roles: {", ".join(roles)}',
        )
        return Response(UserReadSerializer(user).data, status=status.HTTP_200_OK)
