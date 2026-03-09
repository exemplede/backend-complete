# Corrections apportées au Backend

## 1. Django CORS Headers
- Ajouté `django-cors-headers` dans les INSTALLED_APPS
- Ajouté le middleware CORS
- Configuré CORS_ALLOWED_ORIGINS pour le développement
- Mis à jour requirements.txt

## 2. Configuration CORS dans settings.py
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]
CORS_ALLOW_CREDENTIALS = True
```

## 3. Vérifications effectuées
- ✅ Méthode `_parse_date` présente dans InterventionViewSet (ligne 218-223)
- ✅ Méthode `_parse_date` présente dans ActiviteLogViewSet (ligne 344-349)
- ✅ Méthode `_parse_date` présente dans StatistiquesAPIView (ligne 447-452)
- ✅ Toutes les vues sont correctement implémentées
- ✅ Permissions basées sur les rôles fonctionnent correctement

## Installation des dépendances manquantes

```bash
cd backend
pip install django-cors-headers
python manage.py migrate
```

## Créer un super utilisateur

```bash
python manage.py createsuperuser
```

## Créer des utilisateurs avec des rôles via Django Admin

1. Créer des groupes : GestionnaireParticulier, GestionnaireGlobal, Maire
2. Créer des utilisateurs et les assigner à ces groupes

## Lancer le serveur

```bash
python manage.py runserver
```

Le backend sera accessible sur `http://localhost:8000`

## Test de l'API

Vous pouvez utiliser la collection Postman fournie dans `/postman/` pour tester l'API.

## Notes importantes

- Le backend utilise Token Authentication avec support Bearer
- Les tokens sont générés lors de la connexion
- CSRF est désactivé pour les requêtes API
- SQLite est utilisé en développement (fichier db.sqlite3)
