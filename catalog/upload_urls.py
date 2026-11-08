from django.urls import path
from . import upload_views as views
from . import song_uploads

app_name = 'uploads'
urlpatterns = [
    path('song-upload/start/',song_uploads.start,name='song_start'),
    path('song-upload/<uuid:pk>/chunk/',song_uploads.chunk,name='song_chunk'),
    path('song-upload/<uuid:pk>/finish/',song_uploads.finish,name='song_finish'),
    path('song-upload/<uuid:pk>/cancel/',song_uploads.cancel,name='song_cancel'),
    path('',views.library,name='library'),
    path('new/',views.create,name='create'),
    path('<uuid:pk>/',views.detail,name='detail'),
    path('<uuid:pk>/file/',views.file,name='file'),
    path('<uuid:pk>/progress/',views.progress,name='progress'),
    path('<uuid:pk>/delete/',views.delete,name='delete'),
    path('<uuid:pk>/edit/',views.edit,name='edit'),
    path('<uuid:pk>/submit/',views.submit,name='submit'),
    path('<uuid:pk>/withdraw/',views.withdraw,name='withdraw'),
    path('public/<uuid:pk>/',views.public_detail,name='public_detail'),
    path('public/<uuid:pk>/file/',views.public_file,name='public_file'),
    path('review/<uuid:pk>/',views.review_detail,name='review_detail'),
    path('review/<uuid:pk>/file/',views.review_file,name='review_file'),
]
