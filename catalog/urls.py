from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('', views.catalog, name='catalog'),
    path('media/<int:pk>/', views.media_detail, name='media_detail'),
    path('media/<int:pk>/progress/', views.save_progress, name='save_progress'),
    path('clubs/', views.club_list, name='club_list'),
    path('clubs/<int:pk>/', views.club_detail, name='club_detail'),
    path('clubs/<int:pk>/membership/', views.club_membership, name='club_membership'),
    path('clubs/<int:pk>/comments/', views.add_comment, name='add_comment'),
    path('report/<str:kind>/<int:pk>/', views.report, name='report'),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/signup/', views.signup, name='signup'),
]
