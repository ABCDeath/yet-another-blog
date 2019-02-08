from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subscription = models.ManyToManyField('self')

class Post(models.Model):
    caption = models.CharField(max_length=128)
    content_text = models.CharField(max_length=2048)
    pub_date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

