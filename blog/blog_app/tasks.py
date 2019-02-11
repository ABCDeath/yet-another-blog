from django.contrib.sites.models import Site
from django.core.mail import send_mail

from blog.celery import background_worker

from blog_app.models import Post, Profile


@background_worker.task
def send_new_post_notification(post_author, path, destination_email):
    link = ''.join([Site.objects.get_current().domain, path])

    send_mail(
        'Новый пост в вашей ленте',
        f'Пользователь @{post_author} написал новый пост: http://{link}',
        'noreply@yetanotherblog.org',
        [destination_email]
    )
