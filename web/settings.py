import os
import dj_database_url
from pathlib import Path
from dotenv import load_dotenv
from celery.schedules import crontab

from django.contrib.messages import constants as message_constants
MESSAGE_TAGS = {
    message_constants.DEBUG: 'debug',
    message_constants.INFO: 'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR: 'error',  # Убедимся, что error не конфликтует
}

BASE_DIR = Path(__file__).resolve().parent  # Указывает на папку web

# Загружаем .env файл из корневой директории проекта
load_dotenv(os.path.join(BASE_DIR.parent, '.env'))  # parent возвращает путь к корню проекта

# Теперь настройки
SECRET_KEY = 'django-insecure-4#d_&j06lafx$q6$=%j07oc5ufu2)=#)l1%)h2&xdv=q#dg^6w'
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

INSTALLED_APPS = [
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_celery_beat',
    'authapp',
    'traderapp',
    'clientapp',
    'adminapp',
    'paymentapp',
    'authapp.utils',
    "ledger",
    "trades",
    "appeals",
    "notifications",
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'web.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'traderapp.context_processors.user_data',
                'traderapp.context_processors.exchange_rate_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'web.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(default=os.getenv('DATABASE_URL'))
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

CELERY_BROKER_URL = 'redis://localhost:6379/0'  # Адрес брокера (Redis)
CELERY_ACCEPT_CONTENT = ['json']              # Формат сообщений
CELERY_TASK_SERIALIZER = 'json'               # Тип сериализации
CELERY_TIMEZONE = 'UTC'                       # Таймзона для задач

CELERY_BEAT_SCHEDULE = {
    'expire_deposit_requests_task': {
        'task': 'traderapp.tasks.expire_deposit_requests',
        'schedule': crontab(minute='*/1'),  # Запуск каждые 1 минуту
    },
}


LANGUAGE_CODE = 'ru-RU'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR.parent / 'authapp' / 'static',  
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
