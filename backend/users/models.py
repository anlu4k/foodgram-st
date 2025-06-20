from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

class CustomUser(AbstractUser):
    avatar = models.ImageField(
        upload_to='users/avatars/',
        default=None,
        null=True,
        verbose_name='Аватар'
    )
    email = models.EmailField(
        unique=True,
        verbose_name='Электронная почта'
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='Имя пользователя',
        validators=[
            RegexValidator(
                regex=(r"^[\w.@+-]+$"),
                message=(
                    "Имя пользователя может содержать только буквы, "
                    "цифры и знаки @/./+/-/_"
                ),
                code="invalid_username",
            )
        ],
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)
        indexes = [
            models.Index(fields=['username'], name='username_idx'),
            models.Index(fields=['email'], name='email_idx'),
        ]

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='subscriptions')
    following = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='followers')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['user']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'], name='unique user following'
            )
        ]
