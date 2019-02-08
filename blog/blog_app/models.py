from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subscription = models.ManyToManyField('self')

    def __str__(self):
        return f'{self.user.username} ({self.user.get_full_name})'

class Post(models.Model):
    caption = models.CharField(max_length=128)
    content_text = models.CharField(max_length=2048)
    pub_date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.caption}: {self.content_text[:16]} ' \
               f'({self.author.user.username} - {self.pub_date})'
