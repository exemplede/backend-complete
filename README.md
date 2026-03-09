# Green City - Système de Gestion des Espaces Verts et Loisirs

Projet complet de gestion des espaces verts pour les municipalités.

## Description

Application web permettant à une mairie de gérer l'entretien des parcs, des jardins publics et des terrains de sport de la ville.

## Architecture

- **Backend**: Django REST Framework
- **Frontend**: React avec Vite et Tailwind CSS
- **Base de données**: SQLite (dev) / PostgreSQL (production)

## Fonctionnalités

### Répertoire des Espaces
Liste des parcs, squares et stades avec leur superficie et équipements (bancs, balançoires, etc.)

### Planning d'Entretien
Calendrier des tontes de pelouse, de l'arrosage et du ramassage des feuilles

### Gestion du Matériel
Suivi des tondeuses, taille-haies et stocks de fleurs/graines

### Signalement d'Anomalies
Module pour signaler un équipement cassé (ex: "Balançoire cassée au Parc Central")

### Suivi des Équipes
Attribution d'une zone à une équipe d'agents municipaux pour la journée

### Statistiques
Nombre d'interventions réalisées par mois et dépenses en fleurs/plantes

## Rôles utilisateurs

### Gestionnaire Particulier
- Se connecter
- Consulter le planning
- Marquer une intervention comme effectuée
- Signaler une anomalie
- Notifier l'état d'un équipement

### Gestionnaire Global
- Toutes les fonctionnalités du Gestionnaire Particulier
- Créer et gérer les espaces verts
- Programmer les interventions
- Ajouter/réparer le matériel
- Gérer les stocks
- Gérer les équipes
- Consulter les signalements
- Voir les statistiques

### Maire/Administrateur
- Se connecter
- Voir les statistiques
- Voir l'activité globale du système

## Installation

### Backend (Django)

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Frontend (React)

```bash
cd frontend-react
npm install
npm run dev
```

L'application sera accessible sur `http://localhost:3000`

## Configuration

### Backend
- Modifier `green_city/settings.py` pour la configuration
- Base de données SQLite par défaut
- CORS configuré pour accepter les requêtes du frontend

### Frontend
- API URL : `http://localhost:8000/api` (modifiable dans `src/services/api.js`)

## Structure du projet

```
.
├── backend/
│   ├── gestion/           # App principale
│   │   ├── models.py     # Modèles de données
│   │   ├── views.py      # Vues API
│   │   ├── serializers.py
│   │   └── urls.py
│   ├── users/            # Gestion utilisateurs
│   ├── green_city/       # Configuration Django
│   └── manage.py
│
├── frontend-react/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── context/
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
│
└── docs/
    └── Diagramme_Classes_Espaces_Verts.docx
```

## API Endpoints

### Authentification
- POST `/api/users/login/` - Connexion
- POST `/api/users/register/` - Inscription

### Gestion
- `/api/gestion/espaces/` - Espaces verts
- `/api/gestion/equipements/` - Équipements
- `/api/gestion/interventions/` - Interventions
- `/api/gestion/signalements/` - Signalements
- `/api/gestion/equipes/` - Équipes
- `/api/gestion/materiels/` - Matériel
- `/api/gestion/articles-stock/` - Articles en stock
- `/api/gestion/mouvements-stock/` - Mouvements de stock
- `/api/gestion/notifications/` - Notifications
- `/api/gestion/activites/` - Logs d'activité
- `/api/gestion/statistiques/` - Statistiques

## Tests

### Backend
```bash
python manage.py test
```

### Frontend
```bash
npm run test
```

## Déploiement

### Backend
1. Configurer les variables d'environnement
2. Utiliser PostgreSQL en production
3. Collecter les fichiers statiques : `python manage.py collectstatic`
4. Utiliser gunicorn : `gunicorn green_city.wsgi`

### Frontend
1. Builder : `npm run build`
2. Déployer le dossier `dist/` sur un serveur web

## Auteurs

Projet académique - Système de Gestion des Espaces Verts

## Licence

MIT License
