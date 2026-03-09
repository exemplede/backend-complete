# 🚀 Guide de Développement - Green City

## ✅ Ce qui fonctionne actuellement

### Backend Django
- ✅ API complète avec tous les endpoints
- ✅ Authentification par token
- ✅ Gestion des rôles et permissions
- ✅ CORS configuré

### Frontend React
- ✅ Connexion/Déconnexion
- ✅ Dashboard avec statistiques
- ✅ Navigation avec sidebar
- ✅ Page Espaces Verts (complète avec CRUD)
- ✅ Protection des routes
- ✅ Gestion des rôles

## 🔧 Pages à compléter

Les pages suivantes affichent un placeholder "en développement" :
- Interventions
- Signalements  
- Équipements
- Équipes
- Matériel
- Stock
- Statistiques

## 📝 Comment compléter une page

### Exemple : Page Signalements

```jsx
import { useState, useEffect } from 'react';
import { Plus, Edit } from 'lucide-react';
import { signalementService, espaceVertService } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function Signalements() {
  const { isGestionnaireGlobal, isGestionnaireParticulier } = useAuth();
  const [signalements, setSignalements] = useState([]);
  const [espaces, setEspaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    espace: '',
    description: '',
    priorite: 'MOYENNE'
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [sig, esp] = await Promise.all([
        signalementService.getAll(),
        espaceVertService.getAll()
      ]);
      setSignalements(sig.results || []);
      setEspaces(esp.results || []);
    } catch (error) {
      console.error('Erreur:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await signalementService.create(formData);
      setShowModal(false);
      loadData();
    } catch (error) {
      alert('Erreur lors de la création');
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
    </div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Signalements</h1>
        {(isGestionnaireParticulier || isGestionnaireGlobal) && (
          <button onClick={() => setShowModal(true)} className="btn btn-primary flex items-center">
            <Plus className="w-5 h-5 mr-2" />
            Nouveau signalement
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {signalements.map((sig) => (
          <div key={sig.id} className="card">
            <div className="flex justify-between items-start mb-4">
              <h3 className="font-bold text-lg">{sig.espace_nom}</h3>
              <span className={'badge badge-' + (sig.priorite === 'URGENTE' ? 'danger' : 'warning')}>
                {sig.priorite}
              </span>
            </div>
            <p className="text-gray-600 text-sm mb-4">{sig.description}</p>
            <div className="flex justify-between items-center text-sm">
              <span className={'badge badge-' + (sig.statut === 'RESOLU' ? 'success' : 'info')}>
                {sig.statut}
              </span>
              {isGestionnaireGlobal && sig.statut === 'OUVERT' && (
                <button
                  onClick={async () => {
                    await signalementService.changerStatut(sig.id, 'EN_COURS');
                    loadData();
                  }}
                  className="text-blue-600 hover:text-blue-800"
                >
                  Prendre en charge
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Modal de création */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 max-w-md w-full">
            <h2 className="text-2xl font-bold mb-4">Nouveau signalement</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Espace vert</label>
                <select
                  value={formData.espace}
                  onChange={(e) => setFormData({...formData, espace: e.target.value})}
                  className="input-field"
                  required
                >
                  <option value="">Sélectionner...</option>
                  {espaces.map(e => (
                    <option key={e.id} value={e.id}>{e.nom}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  className="input-field"
                  rows="4"
                  required
                  placeholder="Décrivez le problème..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Priorité</label>
                <select
                  value={formData.priorite}
                  onChange={(e) => setFormData({...formData, priorite: e.target.value})}
                  className="input-field"
                >
                  <option value="BASSE">Basse</option>
                  <option value="MOYENNE">Moyenne</option>
                  <option value="HAUTE">Haute</option>
                  <option value="URGENTE">Urgente</option>
                </select>
              </div>
              <div className="flex justify-end space-x-2 pt-4">
                <button type="button" onClick={() => setShowModal(false)} className="btn btn-secondary">
                  Annuler
                </button>
                <button type="submit" className="btn btn-primary">
                  Créer
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
```

## 🎯 Étapes pour compléter chaque page

### 1. Interventions
- Afficher liste des interventions
- Bouton "Marquer effectuée" pour gestionnaires
- Création/modification pour GestionnaireGlobal
- Filtres par statut et date

### 2. Équipements
- Liste des équipements par espace
- Modification de l'état
- Ajout/suppression pour GestionnaireGlobal

### 3. Équipes
- Liste des équipes
- Gestion des membres (ajouter/retirer agents)
- Attribution de zones

### 4. Matériel
- Liste du matériel
- Gestion des états (disponible, en panne, en réparation)
- Ajout/modification

### 5. Stock
- Liste des articles en stock
- Alertes si quantité < seuil
- Mouvements d'entrée/sortie

### 6. Statistiques
- Graphiques avec recharts
- Interventions par mois
- Dépenses
- Signalements résolus

## 💡 Conseils de développement

### Structure d'une page type
```
1. Imports
2. États (useState)
3. Effet de chargement (useEffect)
4. Fonctions de gestion (CRUD)
5. Affichage conditionnel du loading
6. Rendu principal
7. Modal(s) si nécessaire
```

### Services API disponibles
Tous dans `src/services/api.js` :
- `espaceVertService`
- `interventionService`
- `signalementService`
- `equipementService`
- `equipeService`
- `materielService`
- `articleStockService`
- `mouvementStockService`
- `statistiqueService`

### Composants réutilisables à créer (optionnel)
- `Modal.jsx` - Modal générique
- `Table.jsx` - Table avec tri et pagination
- `Badge.jsx` - Badge de statut
- `ConfirmDialog.jsx` - Dialogue de confirmation

## 🐛 Debugging

### Problème : Bouton "Nouvel espace" n'apparaît pas
**Cause** : Le hook `isGestionnaireGlobal` vérifie le groupe de l'utilisateur

**Solution** : Vérifier dans Django Admin que l'utilisateur a bien le groupe `GestionnaireGlobal`

### Problème : Erreur 403 sur les requêtes API
**Cause** : Permissions insuffisantes

**Solution** : Vérifier les rôles dans `green_city/permissions.py` et les groupes de l'utilisateur

### Problème : CORS Error
**Solution** : Vérifier que django-cors-headers est installé et configuré dans settings.py

## 📚 Resources utiles

- [React Docs](https://react.dev)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Lucide Icons](https://lucide.dev)
- [date-fns](https://date-fns.org)
- [Django REST Framework](https://www.django-rest-framework.org)

## 🎓 Prochaines étapes suggérées

1. ✅ Compléter toutes les pages CRUD
2. Ajouter des filtres et recherche
3. Ajouter la pagination
4. Implémenter les graphiques dans Statistiques
5. Ajouter des notifications temps réel
6. Créer un système d'upload de photos pour les signalements
7. Ajouter l'export PDF des rapports
8. Implémenter un calendrier interactif pour les interventions
9. Ajouter un mode sombre
10. Créer une version mobile native (React Native)

Bon développement ! 🚀
