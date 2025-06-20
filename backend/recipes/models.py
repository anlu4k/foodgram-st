from django.db import models
from django.core.validators import MinValueValidator

from users.models import CustomUser

class Ingredient(models.Model):
    name = models.CharField(
        "Название", max_length=128, unique=True
    )
    measurement_unit = models.CharField("Единица измерения", max_length=64)

    class Meta:
        ordering = ["name"]
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="recipes"
    )
    name = models.CharField("Название", max_length=256)
    image = models.ImageField("Фото", upload_to="recipes/")
    text = models.TextField("Описание")
    cooking_time = models.PositiveSmallIntegerField(
        "Время приготовления", validators=[MinValueValidator(1)]
    )
    ingredients = models.ManyToManyField(Ingredient, through="IngredientInRecipe")

    class Meta:
        ordering = ["name"]
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, 
        related_name="ingredient_amounts",
        verbose_name="Рецепт"
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE,
        verbose_name="Ингредиент"
    )
    amount = models.PositiveSmallIntegerField(
        "Количество",
        validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецептах"
        ordering = ["recipe"]
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_recipe_ingredient"
            )
        ]
        indexes = [
            models.Index(fields=["recipe"], name="recipe_idx"),
            models.Index(fields=["ingredient"], name="ingredient_idx"),
        ]

    def __str__(self):
        return f"{self.ingredient.name} - {self.amount} ({self.recipe.name})"


class Favorite(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="favorites"
    )

    class Meta:
        verbose_name = ("Избранное",)
        verbose_name_plural = "Избранные"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique user recipe"
            )
        ]


class ShoppingCart(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="in_cart")

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique user recipe shopping_cart"
            )
        ]
