from django.contrib import admin

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

admin.site.register(EspaceVert)
admin.site.register(Equipement)
admin.site.register(Equipe)
admin.site.register(Intervention)
admin.site.register(Signalement)
admin.site.register(Materiel)
admin.site.register(ArticleStock)
admin.site.register(MouvementStock)
admin.site.register(ActiviteLog)
admin.site.register(Notification)
