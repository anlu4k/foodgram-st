from rest_framework import serializers
from django.db import transaction
from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import UserSerializer

from users.models import Subscription, User

User = get_user_model()

class UserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    class Meta(UserSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                 'last_name', 'avatar', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(user=request.user, following=obj).exists()

    def get_avatar(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None

class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def update(self, instance, validated_data):
        avatar = validated_data.get('avatar')
        if avatar is None:
            raise serializers.ValidationError({'avatar': 'Avatar is required.'})
        instance.avatar = avatar
        instance.save()
        return instance

class SubscriptionUserSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

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