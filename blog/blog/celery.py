from __future__ import absolute_import, unicode_literals
import os
from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')

background_worker = Celery('tasks')
background_worker.config_from_object('django.conf:settings', namespace='CELERY')

background_worker.autodiscover_tasks()
