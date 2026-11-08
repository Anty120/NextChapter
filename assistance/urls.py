from django.urls import path

from . import views

app_name = 'assistance'
urlpatterns = [
    path('lookup/', views.lookup, name='lookup'),
    path('sentence/', views.sentence, name='sentence'),
    path('phonetics/', views.phonetics, name='phonetics'),
    path('explain/', views.explain, name='explain'),
    path('pronounce/', views.pronounce, name='pronounce'),
    path('practice/', views.practice, name='practice'),
]
