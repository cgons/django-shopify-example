import os
from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from dotenv import load_dotenv


class CoreConfig(AppConfig):
    name = 'core'
    SECRET_FILE_PATH = os.path.join(settings.BASE_DIR, '.env.secret')

    def ready(self):
        self._ensure_env_file_exists()
        load_dotenv(self.SECRET_FILE_PATH)

    def _ensure_env_file_exists(self):
        secret_file_exists = os.path.isfile(self.SECRET_FILE_PATH)
        if not secret_file_exists:
            raise ImproperlyConfigured("""
            Secret file (using python-dotenv):
            .env.secret not found in base dir: {}
            """.format(settings.BASE_DIR))
