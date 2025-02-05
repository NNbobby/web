from __future__ import absolute_import, unicode_literals

# Это позволяет загружать Celery при запуске Django
from .celery_app import app as celery_app

__all__ = ('celery_app',)