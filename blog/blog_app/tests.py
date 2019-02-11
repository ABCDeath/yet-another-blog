from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import Profile, Post


class ProfileModelTest(TestCase):
    def test_profile_auto_create(self):
        username = 'user'
        user = User.objects.create_user(username, '', 'testpassword')

        self.assertQuerysetEqual(
            Profile.objects.all(), [f'<Profile: {username} ()>'])

        self.assertEqual(
            user, Profile.objects.get(user__username=username).user)

        self.assertEqual(
            user.profile, Profile.objects.get(user__username=username))

    def test_profile_auto_remove(self):
        username = 'user'
        user = User.objects.create_user(username, '', 'testpassword')
        user.delete()

        self.assertQuerysetEqual(User.objects.filter(username=username), [])
        self.assertQuerysetEqual(Profile.objects.all(), [])

    def test_follow_self(self):
        username = 'user'
        user = User.objects.create_user(username, '', 'testpassword')

        with self.assertRaises(ValidationError):
            user.profile.following.add(user.profile)
            self.assertQuerysetEqual(user.profile.following.all(), [])

    def test_unfollow_read_posts_remove(self):
        username = 'user'
        user = User.objects.create_user(username, '', 'testpassword')

        following_uname = 'following'
        following = User.objects.create_user(
            following_uname, '', 'testpassword')

        user.profile.following.add(following.profile)

        p = Post(caption='c', content_text='t', author=following.profile)
        p.save()

        user.profile.posts_read.add(p)

        self.assertEqual(p, user.profile.posts_read.all()[0])

        user.profile.following.remove(following.profile)

        self.assertQuerysetEqual(user.profile.posts_read.all(), [])

        user.profile.following.add(following.profile)

        self.assertQuerysetEqual(user.profile.posts_read.all(), [])
