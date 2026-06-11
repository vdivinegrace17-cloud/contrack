from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('',                               views.notification_inbox, name='inbox'),
    path('unread/',                        views.unread_count,       name='unread_count'),
    path('messages/<int:application_pk>/', views.message_thread,     name='message_thread'),
    path('messages/<int:application_pk>/send/', views.send_message,  name='send_message'),
]
