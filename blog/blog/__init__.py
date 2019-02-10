from __future__ import absolute_import, unicode_literals

from .celery import background_worker as celery_email_sender

__all__ = ('celery_email_sender',)
