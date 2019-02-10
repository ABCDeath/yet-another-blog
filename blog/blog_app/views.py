from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseRedirect, HttpResponseBadRequest
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import generic
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from .models import Post, Profile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class RootRedirectView(generic.RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return (reverse_lazy('feed') if self.request.user.is_authenticated
                else reverse_lazy('all'))


class AllView(generic.ListView):
    model = Post

    login_url = '/accounts/login/'

    template_name = 'blog_app/feed.html'
    context_object_name = 'posts_feed'
    paginate_by = 10

    def get_queryset(self):
        return Post.objects.prefetch_related('author').order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_profile'] = (self.request.user.profile
                                   if self.request.user.is_authenticated
                                   else None)

        return context


class FeedView(LoginRequiredMixin, AllView):
    model = Post

    login_url = '/accounts/login/'

    template_name = 'blog_app/feed.html'
    context_object_name = 'posts_feed'
    paginate_by = 10

    def get_queryset(self):
        return (Post.objects.prefetch_related('author')
                .filter(author__in=self.request.user.profile.subscription.all())
                .order_by('-pub_date'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_profile'] = (self.request.user.profile
                                   if self.request.user.is_authenticated
                                   else None)

        return context


class BlogView(generic.ListView):
    model = Post

    template_name = 'blog_app/blog.html'
    context_object_name = 'posts'
    paginate_by = 10

    def post(self, request, *args, **kwargs):
        profile = Profile.objects.get(pk=kwargs['profile_pk'])

        if self.request.user.profile.subscription.filter(pk=profile.pk).exists():
            self.request.user.profile.subscription.remove(profile)
        else:
            self.request.user.profile.subscription.add(profile)

        return HttpResponseRedirect(reverse('blog', args=(profile.pk,)))


    def get_queryset(self):
        if not Profile.objects.filter(pk=self.kwargs['profile_pk']).exists():
            raise Http404(f'User profile with pk = {self.kwargs["profile_pk"]} '
                          f'does not exist.')
        return (Post.objects.filter(author__pk=self.kwargs['profile_pk'])
                .order_by('-pub_date'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        profile_pk = self.kwargs['profile_pk']
        profile = (Profile.objects.select_related('user').get(pk=profile_pk))

        context['user_info'] = {
            'username': profile.user.username,
            'full_name': profile.user.get_full_name,
            'postcount': profile.post_set.count(),
            'pk': profile_pk
        }

        if self.request.user.is_authenticated:
            context['user_profile'] = self.request.user.profile
            context['has_subscription'] = (self.request.user.profile
                                           .subscription.filter(pk=profile_pk)
                                           .exists())

        return context


class SubscriptionView(LoginRequiredMixin, generic.ListView):
    model = Profile

    template_name = 'blog_app/subscription.html'
    context_object_name = 'profiles'

    def post(self, request, *args, **kwargs):
        profile = Profile.objects.get(pk=kwargs['profile_pk'])

        if self.request.user.profile.subscription.filter(pk=profile.pk).exists():
            self.request.user.profile.subscription.remove(profile)

        return HttpResponseRedirect(
            reverse('subscription', args=(self.request.user.profile.pk,)))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_profile'] = (self.request.user.profile
                                   if self.request.user.is_authenticated
                                   else None)

        return context

    def get_queryset(self):
        return (self.request.user.profile.subscription.all()
                .order_by('user__username'))


class PostView(generic.DetailView):
    model = Post

    template_name = 'blog_app/post_detail.html'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_profile'] = (self.request.user.profile
                                   if self.request.user.is_authenticated
                                   else None)

        return context


@method_decorator(login_required, name='dispatch')
class PostCreate(generic.CreateView):
    model = Post
    fields = ['caption', 'content_text']

    def form_valid(self, form):
        form.instance.author = Profile.objects.get(user=self.request.user)
        form.save()

        return super().form_valid(form)

    def form_invalid(self, form):
        # TODO
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('post_detail', args=(self.object.pk,))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_profile'] = (self.request.user.profile
                                   if self.request.user.is_authenticated
                                   else None)

        return context


@method_decorator(login_required, name='dispatch')
class PostUpdate(generic.UpdateView):
    model = Post
    fields = ['caption', 'content_text']

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author.user != request.user:
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('post_detail', args=(self.object.pk,))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_profile'] = (self.request.user.profile
                                   if self.request.user.is_authenticated
                                   else None)

        return context


@method_decorator(login_required, name='dispatch')
class PostDelete(generic.DeleteView):
    model = Post

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author.user != request.user:
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            'blog', args=(Profile.objects.get(user=self.request.user).pk,))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_profile'] = (self.request.user.profile
                                   if self.request.user.is_authenticated
                                   else None)

        return context
