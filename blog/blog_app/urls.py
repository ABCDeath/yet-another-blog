from django.urls import path

from . import views

urlpatterns = [
    path('', views.RootRedirectView.as_view(), name='root_redirect'),
    path('all', views.AllView.as_view(), name='all'),
    path('feed', views.FeedView.as_view(), name='feed'),
    path('user/<int:profile_pk>/', views.BlogView.as_view(), name='blog'),
    path('user/<int:profile_pk>/subscription', views.SubscriptionView.as_view(),
         name='subscription'),
    path('post/new', views.PostCreate.as_view(), name='post_create'),
    path('post/<int:pk>/', views.PostView.as_view(), name='post_detail'),
    path('post/<int:pk>/edit', views.PostUpdate.as_view(), name='post_update'),
    path('post/<int:pk>/del', views.PostDelete.as_view(), name='post_delete'),
]
