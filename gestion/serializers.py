from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

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

User = get_user_model()


class EspaceVertSerializer(serializers.ModelSerializer):
    class Meta:
        model = EspaceVert
        fields = '__all__'


class EquipementSerializer(serializers.ModelSerializer):
    espace_nom = serializers.CharField(source='espace.nom', read_only=True)

    class Meta:
        model = Equipement
        fields = '__all__'


class EquipeSerializer(serializers.ModelSerializer):
    agents = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        required=False,
    )

    class Meta:
        model = Equipe
        fields = '__all__'


class MaterielSerializer(serializers.ModelSerializer):
    class Meta:
        model = Materiel
        fields = '__all__'

    def validate(self, attrs):
        total = attrs.get('quantite_totale', getattr(self.instance, 'quantite_totale', 0))
        disponible = attrs.get('quantite_disponible', getattr(self.instance, 'quantite_disponible', 0))
        if disponible > total:
            raise serializers.ValidationError(
                'La quantite disponible ne peut pas depasser la quantite totale.'
            )
        return attrs


class ArticleStockSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleStock
        fields = '__all__'


class InterventionSerializer(serializers.ModelSerializer):
    cree_par_username = serializers.CharField(source='cree_par.username', read_only=True)
    espace_nom = serializers.CharField(source='espace.nom', read_only=True)
    equipe_nom = serializers.CharField(source='equipe.nom', read_only=True)

    class Meta:
        model = Intervention
        fields = '__all__'
        read_only_fields = ['terminee_le', 'cree_par', 'cree_par_username']

    def validate(self, attrs):
        statut = attrs.get('statut', getattr(self.instance, 'statut', Intervention.Statut.PREVUE))
        terminee_le = attrs.get('terminee_le', getattr(self.instance, 'terminee_le', None))
        if statut == Intervention.Statut.TERMINEE and not terminee_le and self.instance:
            attrs['terminee_le'] = timezone.now()
        return attrs


class SignalementSerializer(serializers.ModelSerializer):
    cree_par_username = serializers.CharField(source='cree_par.username', read_only=True)
    espace_nom = serializers.CharField(source='espace.nom', read_only=True)
    equipement_nom = serializers.CharField(source='equipement.nom', read_only=True)

    class Meta:
        model = Signalement
        fields = '__all__'
        read_only_fields = ['cree_par', 'cree_par_username', 'resolved_at']


class MouvementStockSerializer(serializers.ModelSerializer):
    article_nom = serializers.CharField(source='article.nom', read_only=True)

    class Meta:
        model = MouvementStock
        fields = '__all__'
        read_only_fields = ['cree_par']

    def validate(self, attrs):
        article = attrs['article']
        quantite = attrs['quantite']
        mouvement = attrs['type_mouvement']

        if quantite <= Decimal('0'):
            raise serializers.ValidationError('La quantite doit etre strictement positive.')

        if mouvement == MouvementStock.TypeMouvement.SORTIE and article.quantite < quantite:
            raise serializers.ValidationError('Stock insuffisant pour effectuer cette sortie.')

        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            article = validated_data['article']
            quantite = validated_data['quantite']
            mouvement = validated_data['type_mouvement']

            if mouvement == MouvementStock.TypeMouvement.ENTREE:
                article.quantite += quantite
            else:
                article.quantite -= quantite
            article.save(update_fields=['quantite'])

            return super().create(validated_data)


class ActiviteLogSerializer(serializers.ModelSerializer):
    utilisateur_username = serializers.CharField(source='utilisateur.username', read_only=True)

    class Meta:
        model = ActiviteLog
        fields = '__all__'
        read_only_fields = ['created_at']


class NotificationSerializer(serializers.ModelSerializer):
    destinataire_username = serializers.CharField(source='destinataire.username', read_only=True)

    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['created_at']


class ChangerStatutSignalementSerializer(serializers.Serializer):
    statut = serializers.ChoiceField(choices=Signalement.Statut.choices)


class MarquerInterventionEffectueeSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True)
