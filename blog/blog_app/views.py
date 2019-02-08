from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views import generic
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

from .models import Post, Profile


class FeedView(LoginRequiredMixin, generic.ListView):
    model = Post

    login_url = '/accounts/login/'

    template_name = 'blog_app/feed.html'
    context_object_name = 'posts_feed'
    paginate_by = 10

    def get_queryset(self):
        return (Post.objects.prefetch_related('author')
                .filter(author__in=self.request.user.profile.subscription.all())
                .order_by('-pub_date'))

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class BlogView(generic.ListView):
    model = Post

    template_name = 'blog_app/blog.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        if not Profile.objects.filter(pk=self.kwargs['profile_pk']).exists():
            raise Http404(f'User profile with pk = {self.kwargs["profile_pk"]} '
                          f'does not exist.')
        return (Post.objects.filter(author__pk=self.kwargs['profile_pk'])
                .order_by('-pub_date'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        profile = (Profile.objects.select_related('user')
                   .get(pk=self.kwargs['profile_pk']))

        context['user_info'] = {
            'username': profile.user.username,
            'full_name': profile.user.get_full_name,
            'postcount': profile.post_set.count()
        }

        return context


class PostView(generic.DetailView):
    model = Post

    template_name = 'blog_app/post_detail.html'
    context_object_name = 'post'
