#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: Authentication installation and configuration.
# Author(s): Daniel Santillan <daniel.santillan@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2016 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh

info "Configuring allauth ..."

[ -z "$VIRES_HOSTNAME" ] && error "Missing the required VIRES_HOSTNAME variable!"
[ -z "$VIRES_SERVER_HOME" ] && error "Missing the required VIRES_SERVER_HOME variable!"
[ -z "$VIRES_USER" ] && error "Missing the required VIRES_USER variable!"
[ -z "$VIRES_GROUP" ] && error "Missing the required VIRES_GROUP variable!"
[ -z "$VIRES_LOGDIR" ] && error "Missing the required VIRES_LOGDIR variable!"
[ -z "$VIRES_TMPDIR" ] && error "Missing the required VIRES_TMPDIR variable!"

HOSTNAME="$VIRES_HOSTNAME"
INSTANCE="`basename "$VIRES_SERVER_HOME"`"
INSTROOT="`dirname "$VIRES_SERVER_HOME"`"

SETTINGS="${INSTROOT}/${INSTANCE}/${INSTANCE}/settings.py"
URLS="${INSTROOT}/${INSTANCE}/${INSTANCE}/urls.py"
MNGCMD="${INSTROOT}/${INSTANCE}/manage.py"


#-------------------------------------------------------------------------------
# STEP 1: EOXSERVER SETTINGS CONFIGURATION

sudo -u "$VIRES_USER" ex "$SETTINGS" <<END
/^INSTALLED_APPS\s*=/
/^)/
a
# allauth specific apps
INSTALLED_APPS += (
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    #'allauth.socialaccount.providers.github',
    'allauth.socialaccount.providers.facebook',
    #'allauth.socialaccount.providers.twitter',
    #'allauth.socialaccount.providers.dropbox_oauth2'
)
.
/^MIDDLEWARE_CLASSES\s*=/
/^)/a

# allauth specific middleware classes
MIDDLEWARE_CLASSES += (
    'django.middleware.csrf.CsrfViewMiddleware',
    # SessionAuthenticationMiddleware is only available in django 1.7
    # 'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware'
)

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of allauth
    'django.contrib.auth.backends.ModelBackend',
    # allauth specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
)

# Django allauth
SITE_ID = 1 # ID from django.contrib.sites
LOGIN_URL = "accounts/login/"
LOGIN_REDIRECT_URL = "/eoxc/"
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3
ACCOUNT_UNIQUE_EMAIL = True
#ACCOUNT_EMAIL_SUBJECT_PREFIX = [vires.services]
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'http'
ACCOUNT_PASSWORD_MIN_LENGTH = 8
ACCOUNT_LOGIN_ON_PASSWORD_RESET = True
ACCOUNT_USERNAME_REQUIRED = True
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'mandatory'
SOCIALACCOUNT_QUERY_EMAIL = True

TEMPLATE_CONTEXT_PROCESSORS = (
    # Required by allauth template tags
    'django.core.context_processors.request',
    'django.contrib.auth.context_processors.auth'
)
.
wq
END

#-------------------------------------------------------------------------------
# STEP 2: EOXSERVER URLS CONFIGURATION

sudo -u "$VIRES_USER" ex "$URLS" <<END
$ a

#VIRES specific views
urlpatterns += patterns('',
    # enable authentication urls
    url(r'^accounts/', include('allauth.urls')),
)
.
wq
END

#-------------------------------------------------------------------------------
# STEP 3: EOXSERVER DATABASE AUTHENTICATION MODELS INITIALISATION

# setup new database
sudo -u "$VIRES_USER" python "$MNGCMD" syncdb --noinput