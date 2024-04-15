from datetime import timedelta
import os, dj_database_url
from pathlib import Path
from decouple import config, Csv
from django.conf import settings

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = "postgresql://postgres:*dd-FaG6BFBACc6fD3BG1C1Ee55gbc4A@roundhouse.proxy.rlwy.net:47968/railway"

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost', cast=Csv())
ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'authentication.apps.AuthenticationConfig',
    'block_landlord.apps.BlockLandlordConfig',
    'staff_accounts.apps.StaffAccountsConfig',
    'caretaker.apps.CaretakerConfig',
    'admin_api.apps.AdminApiConfig',
    'properties.apps.PropertiesConfig',
    'rest_framework',
    'corsheaders',
    'rest_framework_simplejwt.token_blacklist',
    'tenant_services.apps.TenantServicesConfig',
    'tenant_repairs.apps.TenantRepairsConfig',
    'tenant_marketplace.apps.TenantMarketplaceConfig',
]

AUTH_USER_MODEL = 'authentication.User'

# PASSWORD_HASHERS = [
#   'django.contrib.auth.hashers.PBKDF2PasswordHasher',
#   'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
#   'django.contrib.auth.hashers.Argon2PasswordHasher',
#   'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
#   'django.contrib.auth.hashers.BCryptPasswordHasher',
#   'django.contrib.auth.hashers.SHA1PasswordHasher',
#   'django.contrib.auth.hashers.MD5PasswordHasher',
#   'django.contrib.auth.hashers.UnsaltedSHA1PasswordHasher',
#   'django.contrib.auth.hashers.UnsaltedMD5PasswordHasher',
#   'django.contrib.auth.hashers.CryptPasswordHasher',
# ]

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': settings.SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,


    'AUTH_HEADER_TYPES': ('Bearer', 'JWT'),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}
CSRF_TRUSTED_ORIGINS = ['https://smartnyumbabackup-production.up.railway.app','https://api.smartnyumba.com']

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )

}
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
]

ROOT_URLCONF = 'smartnyumba_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR,'templates')],
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

WSGI_APPLICATION = 'smartnyumba_system.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config("DATABASE_NAME"),
        'USER': config("DATABASE_USER"),
        'PASSWORD': config("DATABASE_PASSWORD"),
        'HOST': config("DATABASE_HOST"),
        'PORT': '3306',
    }
}


# DATABASES = {
#   'default': dj_database_url.config(default=DATABASE_URL, conn_max_age = 1800),
# }




# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/


# STATIC_URL = '/static/'
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
STATICFILES_STORAGE="whitenoise.storage.CompressedManifestStaticFilesStorage"
# MEDIA_URL = '/media/'
# STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
# MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# SMTP CONFIGURATIONS
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST")
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL")
SERVER_EMAIL = config("SERVER_EMAIL")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = config("EMAIL_USE_TLS",default=False, cast=bool)
EMAIL_USE_SSL = config("EMAIL_USE_SSL",default=True, cast=bool)
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)

SAFARICOM_AUTH_ENDPOINT=config('SAFARICOM_AUTH_ENDPOINT')
SAFARICOM_AUTH_KEY=config('SAFARICOM_AUTH_KEY')
SAFARICOM_AUTH_CONSUMER_SECRET=config('SAFARICOM_AUTH_CONSUMER_SECRET')
SAFARICOM_STK_PUSH=config('SAFARICOM_STK_PUSH')
SAFARICOM_PASS_KEY=config('SAFARICOM_PASS_KEY')
BUSINESS_SHORT_CODE=config('BUSINESS_SHORT_CODE')

STRIPE_SECRET_KEY=config('STRIPE_SECRET_KEY')
SUCCESS_URL=config('SUCCESS_URL')
CANCEL_URL=config('CANCEL_URL')
