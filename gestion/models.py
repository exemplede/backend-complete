from django.conf import settings
from django.db import models
from django.utils import timezone


class EspaceVert(models.Model):
    class TypeEspace(models.TextChoices):
        PARC = 'PARC', 'Parc'
        JARDIN = 'JARDIN', 'Jardin public'
        SQUARE = 'SQUARE', 'Square'
        STADE = 'STADE', 'Stade'

    nom = models.CharField(max_length=120, unique=True)
    type_espace = models.CharField(max_length=20, choices=TypeEspace.choices)
    superficie_m2 = models.DecimalField(max_digits=10, decimal_places=2)
    adresse = models.CharField(max_length=255, blank=True)
    zone = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nom']
        verbose_name = 'Espace vert'
        verbose_name_plural = 'Espaces verts'

    def __str__(self):
        return self.nom


class Equipement(models.Model):
    class Etat(models.TextChoices):
        BON = 'BON', 'Bon'
        USE = 'USE', 'Use'
        CASSE = 'CASSE', 'Casse'

    espace = models.ForeignKey(EspaceVert, related_name='equipements', on_delete=models.CASCADE)
    nom = models.CharField(max_length=120)
    quantite = models.PositiveIntegerField(default=1)
    etat = models.CharField(max_length=20, choices=Etat.choices, default=Etat.BON)
    details = models.TextField(blank=True)

    class Meta:
        unique_together = ('espace', 'nom')
        ordering = ['espace__nom', 'nom']

    def __str__(self):
        return f'{self.nom} ({self.espace.nom})'


class Equipe(models.Model):
    nom = models.CharField(max_length=120, unique=True)
    zone_assignee = models.CharField(max_length=120, blank=True)
    agents = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='equipes', blank=True)

    class Meta:
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Materiel(models.Model):
    class Categorie(models.TextChoices):
        TONDEUSE = 'TONDEUSE', 'Tondeuse'
        TAILLE_HAIE = 'TAILLE_HAIE', 'Taille-haie'
        AUTRE = 'AUTRE', 'Autre'

    class Etat(models.TextChoices):
        DISPONIBLE = 'DISPONIBLE', 'Disponible'
        EN_PANNE = 'EN_PANNE', 'En panne'
        EN_REPARATION = 'EN_REPARATION', 'En reparation'
        HORS_SERVICE = 'HORS_SERVICE', 'Hors service'

    nom = models.CharField(max_length=120)
    categorie = models.CharField(max_length=30, choices=Categorie.choices)
    etat = models.CharField(max_length=30, choices=Etat.choices, default=Etat.DISPONIBLE)
    quantite_totale = models.PositiveIntegerField(default=1)
    quantite_disponible = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('nom', 'categorie')
        ordering = ['nom']

    def __str__(self):
        return self.nom


class ArticleStock(models.Model):
    class Unite(models.TextChoices):
        KG = 'KG', 'kg'
        UNITE = 'UNITE', 'unite'
        LITRE = 'LITRE', 'litre'

    nom = models.CharField(max_length=120, unique=True)
    unite = models.CharField(max_length=10, choices=Unite.choices, default=Unite.UNITE)
    quantite = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    seuil_alerte = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Intervention(models.Model):
    class TypeIntervention(models.TextChoices):
        TONTE = 'TONTE', 'Tonte de pelouse'
        ARROSAGE = 'ARROSAGE', 'Arrosage'
        FEUILLES = 'FEUILLES', 'Ramassage des feuilles'
        REPARATION = 'REPARATION', 'Reparation'
        AUTRE = 'AUTRE', 'Autre'

    class Statut(models.TextChoices):
        PREVUE = 'PREVUE', 'Prevue'
        EN_COURS = 'EN_COURS', 'En cours'
        TERMINEE = 'TERMINEE', 'Terminee'
        ANNULEE = 'ANNULEE', 'Annulee'

    type_intervention = models.CharField(max_length=30, choices=TypeIntervention.choices)
    espace = models.ForeignKey(EspaceVert, related_name='interventions', on_delete=models.CASCADE)
    equipe = models.ForeignKey(
        Equipe,
        related_name='interventions',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    planifiee_le = models.DateTimeField()
    terminee_le = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.PREVUE)
    cout = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='interventions_creees',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-planifiee_le']

    def marquer_terminee(self):
        self.statut = self.Statut.TERMINEE
        self.terminee_le = timezone.now()

    def __str__(self):
        return f'{self.type_intervention} - {self.espace.nom}'


class Signalement(models.Model):
    class Priorite(models.TextChoices):
        BASSE = 'BASSE', 'Basse'
        MOYENNE = 'MOYENNE', 'Moyenne'
        HAUTE = 'HAUTE', 'Haute'
        URGENTE = 'URGENTE', 'Urgente'

    class Statut(models.TextChoices):
        OUVERT = 'OUVERT', 'Ouvert'
        EN_COURS = 'EN_COURS', 'En cours'
        RESOLU = 'RESOLU', 'Resolu'
        REJETE = 'REJETE', 'Rejete'

    espace = models.ForeignKey(EspaceVert, related_name='signalements', on_delete=models.CASCADE)
    equipement = models.ForeignKey(
        Equipement,
        related_name='signalements',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    description = models.TextField()
    priorite = models.CharField(max_length=20, choices=Priorite.choices, default=Priorite.MOYENNE)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.OUVERT)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='signalements_crees',
        on_delete=models.SET_NULL,
        null=True,
    )
    assigne_a = models.ForeignKey(
        Equipe,
        related_name='signalements',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Signalement #{self.id} - {self.espace.nom}'


class MouvementStock(models.Model):
    class TypeMouvement(models.TextChoices):
        ENTREE = 'ENTREE', 'Entree'
        SORTIE = 'SORTIE', 'Sortie'

    article = models.ForeignKey(ArticleStock, related_name='mouvements', on_delete=models.CASCADE)
    type_mouvement = models.CharField(max_length=10, choices=TypeMouvement.choices)
    quantite = models.DecimalField(max_digits=10, decimal_places=2)
    motif = models.CharField(max_length=255, blank=True)
    date_mouvement = models.DateTimeField(default=timezone.now)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='mouvements_stock_crees',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['-date_mouvement']

    def __str__(self):
        return f'{self.type_mouvement} {self.quantite} {self.article.nom}'


class ActiviteLog(models.Model):
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='activites',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=120)
    objet_type = models.CharField(max_length=120)
    objet_id = models.PositiveIntegerField(null=True, blank=True)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.action} ({self.created_at:%Y-%m-%d %H:%M})'


class Notification(models.Model):
    class TypeNotification(models.TextChoices):
        INTERVENTION = 'INTERVENTION', 'Intervention'
        SIGNALEMENT = 'SIGNALEMENT', 'Signalement'
        STOCK = 'STOCK', 'Stock'
        SYSTEME = 'SYSTEME', 'Systeme'

    destinataire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='notifications',
        on_delete=models.CASCADE,
    )
    type_notification = models.CharField(max_length=20, choices=TypeNotification.choices)
    titre = models.CharField(max_length=180)
    message = models.TextField()
    url_cible = models.CharField(max_length=255, blank=True)
    lu = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.titre} -> {self.destinataire}'
