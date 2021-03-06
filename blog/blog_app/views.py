from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.http import Http404, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import generic

from celery import group

from .models import Profile, Post
from .tasks import send_new_post_notification


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


@receiver(m2m_changed, sender=Profile.following.through)
def profile_update(sender, instance, action, pk_set, **kwargs):
    if action == 'pre_add':
        if instance.pk == list(pk_set)[0]:
            raise ValidationError('You can not follow yourself')
    elif action == 'post_remove':
        posts_read = instance.posts_read.filter(author__id__in=pk_set)
        instance.posts_read.remove(*posts_read)


@receiver(post_save, sender=Post)
def post_create_email_followers(sender, instance, created, **kwargs):
    if created:
        followers_email = list(
            Profile.objects.select_related('user')
                .filter(following=instance.author)
                .values_list('user__email', flat=True))

        path = str(reverse_lazy('post_detail', args=(instance.pk,)))

        send_tasks = group([
            send_new_post_notification.si(str(instance.author), path, email)
            for email in followers_email])
        send_tasks()


class BaseView(generic.base.ContextMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_profile'] = (self.request.user.profile
                                   if self.request.user.is_authenticated
                                   else None)

        return context


class RootRedirectView(generic.RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return (reverse_lazy('feed') if self.request.user.is_authenticated
                else reverse_lazy('all'))


class AllView(BaseView, generic.ListView):
    model = Post

    login_url = '/accounts/login/'

    template_name = 'blog_app/all_posts.html'
    context_object_name = 'posts_feed'
    paginate_by = 10

    def get_queryset(self):
        return Post.objects.select_related('author').order_by('-pub_date')


class FeedView(LoginRequiredMixin, AllView):
    model = Post

    login_url = '/accounts/login/'

    template_name = 'blog_app/feed.html'
    context_object_name = 'posts_feed'

    def get_queryset(self):
        return (Post.objects.select_related('author')
                .filter(author__in=self.request.user.profile.following.all())
                .order_by('-pub_date'))


@method_decorator(login_required, name='dispatch')
class ProfileUpdateView(generic.UpdateView):
    model = Profile

    def _mark_post(self, user_profile, post_pk):
        post = get_object_or_404(Post, pk=post_pk)
        if post in user_profile.posts_read.all():
            user_profile.posts_read.remove(post)
        else:
            user_profile.posts_read.add(post)

    def _manage_follow(self, user_profile, follow, unfollow):
        profile = Profile.objects.get(pk=follow or unfollow)

        if user_profile == profile:
            return

        if follow:
            user_profile.following.add(profile)
        elif unfollow:
            user_profile.following.remove(profile)

    def get(self, request, *args, **kwargs):
        raise Http404

    def post(self, request, *args, **kwargs):
        if 'mark_post_read' in request.POST:
            self._mark_post(self.request.user.profile,
                            request.POST['mark_post_read'])
        elif 'follow' in request.POST or 'unfollow' in request.POST:
            self._manage_follow(
                self.request.user.profile,
                request.POST.get('follow'), request.POST.get('unfollow'))
        else:
            return HttpResponseBadRequest(f'Bad request: {request.path}')

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


class BlogView(BaseView, generic.ListView):
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

        profile_pk = self.kwargs['profile_pk']
        profile = (Profile.objects.select_related('user').get(pk=profile_pk))

        context['user_info'] = {
            'username': profile.user.username,
            'full_name': profile.user.get_full_name,
            'postcount': profile.post_set.count(),
            'pk': profile_pk
        }

        if self.request.user.is_authenticated:
            context['is_followed'] = (self.request.user.profile
                                      .following.filter(pk=profile_pk).exists())

        return context


class FollowingView(BaseView, LoginRequiredMixin, generic.ListView):
    model = Profile

    template_name = 'blog_app/following.html'
    context_object_name = 'profiles'

    def get_queryset(self):
        return (self.request.user.profile.following.all()
                .order_by('user__username'))


class PostView(BaseView, generic.DetailView):
    model = Post

    template_name = 'blog_app/post_detail.html'
    context_object_name = 'post'


@method_decorator(login_required, name='dispatch')
class PostCreate(BaseView, generic.CreateView):
    model = Post
    fields = ['caption', 'content_text']

    def form_valid(self, form):
        form.instance.author = Profile.objects.get(user=self.request.user)
        form.save()

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('post_detail', args=(self.object.pk,))


@method_decorator(login_required, name='dispatch')
class PostUpdate(BaseView, generic.UpdateView):
    model = Post
    fields = ['caption', 'content_text']

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author.user != request.user:
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('post_detail', args=(self.object.pk,))


@method_decorator(login_required, name='dispatch')
class PostDelete(BaseView, generic.DeleteView):
    model = Post

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author.user != request.user:
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            'blog', args=(Profile.objects.get(user=self.request.user).pk,))
