"""
Django settings for project_egaz project.
"""

from pathlib import Path
import os  # 🔥 ADD THIS IMPORT

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = 'django-insecure-(3a3^x(l^epb+eh3qk2+)r(9_wzuamb!e%ddi@j&cw$p4i-ox8'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False  # 🔥 KEEP THIS AS FALSE FOR PRODUCTION

ALLOWED_HOSTS = ['back.deploy.tz', 'front.deploy.tz', 'localhost', '127.0.0.1']  # 🔥 SPECIFIC HOSTS

# Use custom user model
AUTH_USER_MODEL = 'egaz_app.User'

# 🔥 MEDIA FILES CONFIGURATION - HAKIKISHA HII IKO SAWA
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # 🔥 USE os.path.join

# 🔥 STATIC FILES CONFIGURATION - IMPORTANT FOR PRODUCTION
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # 🔥 ADD THIS LINE

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'egaz_app.apps.EgazAppConfig',
    'corsheaders',
    'django_celery_beat',
    'django_crontab',
    'django_extensions',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # MUST BE FIRST
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'project_egaz.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'project_egaz.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'project_egaz.db',
    }
}

# 🔥 CORS CONFIGURATION - FIX THESE
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "https://front.deploy.tz"
]

# 🔥 REMOVE OR COMMENT OUT THESE LINES:
# CORS_ALLOW_ALL_ORIGINS = True  # ❌ COMMENT OR REMOVE THIS LINE
# CORS_ALLOW_CREDENTIALS = True   # ❌ COMMENT OR REMOVE THIS LINE

CSRF_TRUSTED_ORIGINS = ['https://front.deploy.tz', 'https://back.deploy.tz']

# Password validation
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

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework configuration
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "egaz_app.authentication.CustomTokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# Email configuration (keep your existing)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'comodoosimba@gmail.com'
EMAIL_HOST_PASSWORD = 'vrof wegz xvsl zrls'
DEFAULT_FROM_EMAIL = 'comodoosimba@gmail.com'

# Cron jobs
CRONJOBS = [
    ('0 16 * * *', 'schedules.cron.daily_apology_job'),
]