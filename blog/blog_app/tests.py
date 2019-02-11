from django.contrib.auth.models import User
from django.test import TestCase

from .models import Profile, Post


class ProfileModelTest(TestCase):
    def test_profile_auto_create(self):
        username = 'test_user'
        user = User.objects.create_user(username, '', 'testpassword')

        self.assertQuerysetEqual(
            Profile.objects.all(), ['<Profile: test_user ()>'])

        self.assertEqual(
            user, Profile.objects.get(user__username=username).user)

        self.assertEqual(
            user.profile, Profile.objects.get(user__username=username))
