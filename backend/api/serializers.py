from rest_framework import serializers
from django.db import transaction
from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import UserSerializer
from recipes.models import (
    Ingredient, 
    IngredientInRecipe,
    Recipe,
    Favorite,
    ShoppingCart
)
from users.models import Subscription, CustomUser

User = get_user_model()

class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    class Meta(UserSerializer.Meta):
        model = CustomUser
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'avatar', 'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(user=user, following=obj).exists()

    def get_avatar(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = CustomUser
        fields = ('avatar',)

    def update(self, instance, validated_data):
        avatar = validated_data.get('avatar')
        if avatar is None:
            raise serializers.ValidationError(
                {'avatar': 'Avatar is required.'}
            )

        instance.avatar = avatar
        instance.save()
        return instance


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)


class SubscriptionUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        )

    def get_is_subscribed(self, obj):
        return True

    def get_recipes(self, obj):
        request = self.context.get('request')
        try:
            limit = int(request.query_params.get('recipes_limit'))
        except (ValueError, TypeError):
            limit = None
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:limit]
        return ShortRecipeSerializer(recipes, many=True, context=self.context).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'
        read_only_fields = ('id',)


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipeSerializer(
        source='ingredient_amounts',
        many=True
    )
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField(required=False)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )
        read_only_fields = ('id', 'author', 'is_favorited',
                            'is_in_shopping_cart')

    @transaction.atomic
    def create(self, validated_data):
        ingredient_data = validated_data.pop('ingredient_amounts')
        recipe = Recipe.objects.create(**validated_data)
        self._set_ingredients(recipe, ingredient_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredient_data = validated_data.pop('ingredient_amounts', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if ingredient_data is not None:
            instance.ingredient_amounts.all().delete()
            self._set_ingredients(instance, ingredient_data)
        return instance

    def _set_ingredients(self, recipe, ingredient_data):
        IngredientInRecipe.objects.bulk_create([
            IngredientInRecipe(
                recipe=recipe,
                ingredient=ingredient_data['ingredient'],
                amount=ingredient_data['amount']
            )
            for ingredient_data in ingredient_data
        ])

    # Ошибка, если поле image есть, но у него пустое значение
    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError('У рецепта должна быть картинка')
        return value

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'У рецепта должен быть хотя бы один ингредиент'}
            )

        seen_ingredients = set()
        for ingr in ingredients:
            ingr_id = ingr.get('id')
            ingr_amount = ingr.get('amount')

            if ingr_id in seen_ingredients:
                raise serializers.ValidationError(
                    {'ingredients': 'Ингредиенты должны быть уникальными'}
                )
            seen_ingredients.add(ingr_id)

            if int(ingr_amount) <= 0:
                raise serializers.ValidationError(
                    {'ingredients': 'Количество ингредиента должно быть больше нуля'}
                )
            
        # Проверка только в случае создания рецепта (не нарушает редактирование)
        if self.instance is None:
            image_in_data = 'image' in self.initial_data
            image_value = self.initial_data.get('image')
            
            if not image_in_data or not image_value:
                raise serializers.ValidationError(
                    {'image': 'У рецепта должна быть картинка'}
                )
            
        return data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return Favorite.objects.filter(
            user=request.user.id,
            recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return ShoppingCart.objects.filter(
            user=request.user.id,
            recipe=obj
        ).exists()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['image'] = instance.image.url
        return representation
