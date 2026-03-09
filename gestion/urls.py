from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ActiviteLogViewSet,
    ArticleStockViewSet,
    EquipeViewSet,
    EquipementViewSet,
    EspaceVertViewSet,
    InterventionViewSet,
    MaterielViewSet,
    MouvementStockViewSet,
    NotificationViewSet,
    SignalementViewSet,
    StatistiquesAPIView,
)

router = DefaultRouter()
router.register(r'espaces', EspaceVertViewSet, basename='espaces')
router.register(r'equipements', EquipementViewSet, basename='equipements')
router.register(r'equipes', EquipeViewSet, basename='equipes')
router.register(r'interventions', InterventionViewSet, basename='interventions')
router.register(r'signalements', SignalementViewSet, basename='signalements')
router.register(r'materiels', MaterielViewSet, basename='materiels')
router.register(r'articles-stock', ArticleStockViewSet, basename='articles-stock')
router.register(r'mouvements-stock', MouvementStockViewSet, basename='mouvements-stock')
router.register(r'activites', ActiviteLogViewSet, basename='activites')
router.register(r'notifications', NotificationViewSet, basename='notifications')

urlpatterns = [
    path('', include(router.urls)),
    path('statistiques/', StatistiquesAPIView.as_view(), name='statistiques'),
]
