import os
import dj_database_url


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'group_ordering_app',
]

ALLOWED_HOSTS = ['*']
# Supabase PostgreSQL Database Configuration
DATABASE_URL="postgresql://postgres.uxedjorelcqsirkwlwev:[89QzEX6bs5Vnr_+]@aws-0-eu-west-2.pooler.supabase.com:5432/postgres"

# Database configuration
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get(DATABASE_URL),
        conn_max_age=600,
        conn_health_checks=True,
    )
}