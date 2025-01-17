"""
Django settings for CSSANet project.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os
import datetime

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
DEBUG = False
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_DIR = os.path.dirname(PROJECT_DIR)
SECRET_KEY = '=3qm1_ubi+$_bzvcj0yxoq+52q!l9+k*za&s06@z1#pee9bd2l'

SITE_ID = 1

# Application definition
INSTALLED_APPS = [
    'EventAPI',
    'CommunicateManager',
    'LegacyDataAPI',
    'RecruitAPI',
    'UserAuthAPI',
    'FinanceAPI',
    'OrganisationMgr',    
    'PublicSite',
    'myCSSAhub',
    'BlogAPI',
    'FlexForm',
    'PhotoCompetition',
    'PrizeAPI',
    'mail_owl',
    'MobileAppAPI',
    'CommunityAPI',

    ## RESTful Support
    'rest_framework',
    'rest_framework.authtoken',
    'rest_auth',
    'rest_framework_simplejwt',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'social_django',

    'django.contrib.contenttypes',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'drf_yasg', # swagger

    ## Server add-in
    'gunicorn',
    'widget_tweaks',
    'django_filters',
    'guard_angel',
    'storages',
    'redis',
    'sorl.thumbnail',
    'debug_toolbar',
]

INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
#    'guard_angel.middleware.HttpRequestLogMiddleware',
]

ROOT_URLCONF = 'CSSANet.urls'

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
            ],
        },
    },
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.TokenAuthentication'
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser', 
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated'
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
}


AUTH_USER_MODEL = 'UserAuthAPI.User'
AUTH_PROFILE_MODULE = "UserAuthAPI.UserProfile"

AUTHENTICATION_BACKENDS = (
    'social_core.backends.weixin.WeixinOAuth2',
    # Needed to login by username in Django admin, regardless of `allauth`
    'UserAuthAPI.authBackend.ModelBackend'
#    'UserAuthAPI.auth.EmailOrUsernameModelBackend',
)

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': datetime.timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': datetime.timedelta(days=30)
}

REST_AUTH_SERIALIZERS = {
    'LOGIN_SERIALIZER': 'UserAuthAPI.serializers.APILoginSerializer',

}
REST_AUTH_REGISTER_SERIALIZERS = {
    "REGISTER_SERIALIZER": "UserAuthAPI.serializers.AcccountInitRegisterSerializer",
}

# Base URL to use when referring to full URLs within the Wagtail admin backend -
# e.g. in notification emails. Don't include '/admin' or a trailing slash
BASE_URL = 'http://cssaunimelb.com'

# Login Settings
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_AUTHENTICATION_METHOD = None
ACCOUNT_EMAIL_VERIFICATION = 'none'

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_EMAIL_FIELD = 'email'
ACCOUNT_LOGOUT_ON_GET = True

WSGI_APPLICATION = 'CSSANet.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

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

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

USE_TZ = True

TIME_ZONE = 'Australia/Melbourne'

USE_I18N = True

USE_L10N = True

LANGUAGE_CODE = 'zh-hans'

### Logging configuration
LOGGING = {
	'version': 1,
	'disable_existing_loggers': False,
	'filters': {
		'require_debug_false': {
			'()': 'django.utils.log.RequireDebugFalse',
		},
		'require_debug_true': {
			'()': 'django.utils.log.RequireDebugTrue',
		},
	},
	'formatters': {
		'django.server': {
			'()': 'django.utils.log.ServerFormatter',
			'format': '[%(server_time)s] %(message)s',
		},
        'console': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        },
	},
	'handlers': {
		'console': {
			'level': 'INFO',
			'filters': ['require_debug_true'],
			'class': 'logging.StreamHandler',
            'formatter': 'console',
		},
		'console_debug_false': {
			'level': 'ERROR',
			'filters': ['require_debug_false'],
			'class': 'logging.StreamHandler',
            'formatter': 'console',
		},
		'django.server': {
			'level': 'INFO',
			'class': 'logging.StreamHandler',
			'formatter': 'django.server',
		},
		'mail_admins': {
			'level': 'ERROR',
			'filters': ['require_debug_false'],
			'class': 'django.utils.log.AdminEmailHandler'
		}
	},
	'loggers': {
		'django': {
			'handlers': ['console', 'console_debug_false', 'mail_admins'],
			'level': 'INFO',
		},
		'django.server': {
			'handlers': ['django.server'],
			'level': 'INFO',
			'propagate': False,
		},
        'app': { # App logger 
            'handlers': ['console', 'console_debug_false'],
            'level': 'DEBUG',
        },
	}
}
ADMINS = [('Master Inbox', 'information@cssaunimelb.com'), ('Lead Engineer', 'joshlubox@gmail.com')]

SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': False,
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    },
}

# 小程序API相关
MINIPROGRAM_APPID = '' 
MINIPROGRAM_SECRET ='' 