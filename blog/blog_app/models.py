from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    following = models.ManyToManyField('self', symmetrical=False)
    posts_read = models.ManyToManyField('Post')

    def __str__(self):
        return f'{self.user.username} ({self.user.get_full_name()})'


class Post(models.Model):
    caption = models.CharField(max_length=128)
    content_text = models.TextField()
    pub_date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.caption}: {self.content_text[:16]} ' \
               f'({self.author.user.username} - {self.pub_date})'
