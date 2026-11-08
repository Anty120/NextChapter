from django.urls import path

from . import views

app_name = 'assistance'
urlpatterns = [
    path('explain/', views.explain, name='explain'),
    path('pronounce/', views.pronounce, name='pronounce'),
    path('practice/', views.practice, name='practice'),
]
