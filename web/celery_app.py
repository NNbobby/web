from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Указываем настройки Django по умолчанию
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')

# Создаем экземпляр Celery
app = Celery('web')

# Загружаем настройки из файла settings.py (все, что начинается с CELERY_)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически находит задачи в приложениях, указанных в INSTALLED_APPS
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
