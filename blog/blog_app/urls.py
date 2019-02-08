from django.urls import path

from . import views

urlpatterns = [
    path('', views.FeedView.as_view(), name='feed'),
    path('<int:profile_pk>/', views.BlogView.as_view(), name='blog')
]
