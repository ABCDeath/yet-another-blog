from django.urls import path

from . import views

urlpatterns = [
    path('', views.FeedView.as_view(), name='feed'),
    path('user/<int:profile_pk>/', views.BlogView.as_view(), name='blog'),
    path('post/<int:pk>', views.PostView.as_view(), name='post_detail')
]
