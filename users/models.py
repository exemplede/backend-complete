from django.conf import settings
from django.db import models

from green_city.permissions import (
    ROLE_GESTIONNAIRE_GLOBAL,
    ROLE_GESTIONNAIRE_PARTICULIER,
    ROLE_MAIRE,
)


class UserProfile(models.Model):
    ROLE_CHOICES = [
        (ROLE_GESTIONNAIRE_PARTICULIER, ROLE_GESTIONNAIRE_PARTICULIER),
        (ROLE_GESTIONNAIRE_GLOBAL, ROLE_GESTIONNAIRE_GLOBAL),
        (ROLE_MAIRE, ROLE_MAIRE),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    matricule = models.CharField(max_length=50, unique=True, null=True, blank=True)
    telephone = models.CharField(max_length=30, blank=True)
    fonction = models.CharField(max_length=120, blank=True)
    zone_reference = models.CharField(max_length=120, blank=True)
    date_embauche = models.DateField(null=True, blank=True)
    role_principal = models.CharField(max_length=40, choices=ROLE_CHOICES, blank=True)
    actif_terrain = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__username']

    def __str__(self):
        return f'Profil {self.user.username}'
