Foodgram
Foodgram, «Продуктовый помощник». Онлайн-сервис и API для публикации и обмена рецептами. Пользователи могут подписываться на авторов, добавлять рецепты в «Избранное» и скачивать сводный список продуктов для выбранных блюд.

Локальный запуск с Docker
1. Клонирование репозитория
git clone https://github.com/SaveliyKrivov/foodgram-st.git
cd foodgram-st
2. Создание и настройка .env файла
В корне проекта создайте файл .env со следующим содержимым:

POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
DB_HOST=db
DB_PORT=5432
SECRET_KEY=your_django_secret_key
DEBUG=False
ALLOWED_HOSTS=127.0.0.1,localhost
3. Сборка и запуск контейнеров
Перейдите в директорию infra/ и выполните:

docker-compose up -d --build
4. Применение миграций и сбор статики
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py collectstatic --noinput
5. Создание суперпользователя
docker-compose exec backend python manage.py createsuperuser
6. Загрузка данных
Загрузите ингредиенты, пользователей и рецепты:

docker-compose exec backend python manage.py load_ingredients
docker-compose exec backend python manage.py load_users
docker-compose exec backend python manage.py load_recipes

7. Доступ к приложению
Frontend: http://localhost/
Админка: http://localhost/admin/
API: http://localhost/api/
