from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

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

    def test_follower_profile_cleanup(self):
        username = 'user'
        user = User.objects.create_user(username, '', 'testpassword')

        following_uname = 'following'
        following = User.objects.create_user(
            following_uname, '', 'testpassword')

        user.profile.following.add(following.profile)

        p = Post(caption='c', content_text='t', author=following.profile)
        p.save()

        user.profile.posts_read.add(p)

        following.delete()

        self.assertQuerysetEqual(user.profile.posts_read.all(), [])
        self.assertQuerysetEqual(user.profile.following.all(), [])

    def test_follows(self):
        username = 'user'
        user1 = User.objects.create_user(username + '1', '', 'testpassword')
        user2 = User.objects.create_user(username + '2', '', 'testpassword')
        user3 = User.objects.create_user(username + '3', '', 'testpassword')

        user1.profile.following.add(user2.profile, user3.profile)
        user2.profile.following.add(user1.profile)
        user3.profile.following.add(user2.profile)

        self.assertQuerysetEqual(
            user1.profile.following.all().order_by('user__username'),
            ['<Profile: user2 ()>', '<Profile: user3 ()>'])
        self.assertQuerysetEqual(
            user2.profile.following.all().order_by('user__username'),
            ['<Profile: user1 ()>'])
        self.assertQuerysetEqual(
            user3.profile.following.all().order_by('user__username'),
            ['<Profile: user2 ()>'])


class PostModelTest(TestCase):
    def test_auto_remove_user_posts(self):
        username = 'user'
        user = User.objects.create_user(username, '', 'testpassword')

        p = Post(caption='c', content_text='t', author=user.profile)
        p.save()

        self.assertEqual(Post.objects.count(), 1)

        user.delete()

        self.assertEqual(Post.objects.count(), 0)


class RootRedirectViewTest(TestCase):
    def test_redirect_not_logged_in(self):
        self.assertRedirects(
            self.client.get(reverse('root_redirect')), reverse('all'))

    def test_redirect_logged_in(self):
        username = 'user'
        user = User.objects.create_user(username, '', 'testpassword')
        self.client.force_login(user=user)
        self.assertRedirects(
            self.client.get(reverse('root_redirect')), reverse('feed'))
