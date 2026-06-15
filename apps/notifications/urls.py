from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('unread/',                        views.unread_count,          name='unread_count'),
    path('list/',                          views.notification_list_json, name='list'),
    path('mark-read/',                     views.mark_all_read,          name='mark_all_read'),
    path('messages/<int:application_pk>/', views.message_thread,         name='message_thread'),
    path('messages/<int:application_pk>/send/', views.send_message,      name='send_message'),
]
