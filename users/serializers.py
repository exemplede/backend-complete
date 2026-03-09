from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from rest_framework import serializers

from green_city.permissions import AVAILABLE_ROLES
from .models import UserProfile

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        exclude = ['user']


class UserReadSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_active',
            'is_staff',
            'roles',
            'profile',
            'date_joined',
            'last_login',
        ]

    def get_roles(self, obj):
        return list(obj.groups.values_list('name', flat=True))


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    roles = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
    profile = UserProfileSerializer(required=False)

    class Meta:
        model = User
        fields = [
            'username',
            'password',
            'first_name',
            'last_name',
            'email',
            'is_active',
            'roles',
            'profile',
        ]

    def validate_roles(self, value):
        invalid = [role for role in value if role not in AVAILABLE_ROLES]
        if invalid:
            raise serializers.ValidationError(f'Roles invalides: {", ".join(invalid)}')
        return value

    def create(self, validated_data):
        roles = validated_data.pop('roles', [])
        profile_data = validated_data.pop('profile', {})
        password = validated_data.pop('password')
        with transaction.atomic():
            user = User(**validated_data)
            user.set_password(password)
            user.save()
            if roles:
                groups = Group.objects.filter(name__in=roles)
                user.groups.set(groups)
            profile = user.profile
            for field, value in profile_data.items():
                setattr(profile, field, value)
            profile.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    roles = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
    profile = UserProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'is_active', 'roles', 'profile']

    def validate_roles(self, value):
        invalid = [role for role in value if role not in AVAILABLE_ROLES]
        if invalid:
            raise serializers.ValidationError(f'Roles invalides: {", ".join(invalid)}')
        return value

    def update(self, instance, validated_data):
        roles = validated_data.pop('roles', None)
        profile_data = validated_data.pop('profile', None)

        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        if roles is not None:
            instance.groups.set(Group.objects.filter(name__in=roles))

        if profile_data:
            profile = instance.profile
            for field, value in profile_data.items():
                setattr(profile, field, value)
            profile.save()

        return instance


class RoleAssignmentSerializer(serializers.Serializer):
    roles = serializers.ListField(child=serializers.CharField(), allow_empty=False)

    def validate_roles(self, value):
        invalid = [role for role in value if role not in AVAILABLE_ROLES]
        if invalid:
            raise serializers.ValidationError(f'Roles invalides: {", ".join(invalid)}')
        return value


class MeUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    telephone = serializers.CharField(required=False, allow_blank=True, max_length=30)
    fonction = serializers.CharField(required=False, allow_blank=True, max_length=120)
    zone_reference = serializers.CharField(required=False, allow_blank=True, max_length=120)
    date_embauche = serializers.DateField(required=False, allow_null=True)
    actif_terrain = serializers.BooleanField(required=False)

    def update(self, instance, validated_data):
        profile_fields = ['telephone', 'fonction', 'zone_reference', 'date_embauche', 'actif_terrain']

        for field in ['first_name', 'last_name', 'email']:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()

        profile = instance.profile
        for field in profile_fields:
            if field in validated_data:
                setattr(profile, field, validated_data[field])
        profile.save()
        return instance

    def create(self, validated_data):
        raise NotImplementedError


class PasswordChangeSerializer(serializers.Serializer):
    ancien_mot_de_passe = serializers.CharField()
    nouveau_mot_de_passe = serializers.CharField(min_length=8)
