from rest_framework.permissions import BasePermission

ROLE_GESTIONNAIRE_PARTICULIER = 'GestionnaireParticulier'
ROLE_GESTIONNAIRE_GLOBAL = 'GestionnaireGlobal'
ROLE_MAIRE = 'Maire'
AVAILABLE_ROLES = [ROLE_GESTIONNAIRE_PARTICULIER, ROLE_GESTIONNAIRE_GLOBAL, ROLE_MAIRE]


def has_role(user, role_name: str) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name=role_name).exists()


def has_any_role(user, roles: set[str]) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    user_roles = set(user.groups.values_list('name', flat=True))
    return bool(user_roles.intersection(roles))


class IsGestionnaireParticulier(BasePermission):
    def has_permission(self, request, view):
        return has_role(request.user, ROLE_GESTIONNAIRE_PARTICULIER)


class IsGestionnaireGlobal(BasePermission):
    def has_permission(self, request, view):
        return has_role(request.user, ROLE_GESTIONNAIRE_GLOBAL)


class IsMaire(BasePermission):
    def has_permission(self, request, view):
        return has_role(request.user, ROLE_MAIRE)
