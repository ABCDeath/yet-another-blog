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

    def test_follow_self(self):
        username = 'user'
        user = User.objects.create_user(username, '', 'testpassword')

        with self.assertRaises(ValidationError):
            user.profile.following.add(user.profile)
            self.assertQuerysetEqual(user.profile.following.all(), [])
