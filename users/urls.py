from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    LoginAPIView,
    LogoutAPIView,
    MeAPIView,
    MePasswordAPIView,
    RoleListAPIView,
    UserViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('users/login/', LoginAPIView.as_view(), name='users-login'),
    path('users/logout/', LogoutAPIView.as_view(), name='users-logout'),
    path('users/me/', MeAPIView.as_view(), name='users-me'),
    path('users/me/change-password/', MePasswordAPIView.as_view(), name='users-me-change-password'),
    path('users/roles/', RoleListAPIView.as_view(), name='users-roles'),
    path('', include(router.urls)),
]
