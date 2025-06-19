from django.urls import include, path
from rest_framework import routers

from api.views.users import CustomUserViewSet
from api.views.recipes import RecipeViewSet, IngredientViewSet

router = routers.DefaultRouter()
router.register('users', CustomUserViewSet, basename='users')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]