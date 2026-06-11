from django.urls import path
from . import views

app_name = 'communications'

urlpatterns = [
    # ── Notifications ─────────────────────────────────────────────────────────
    path('notifications/',              views.notification_list,  name='notifications'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark_read'),
    path('notifications/read-all/',     views.mark_all_read,     name='mark_all_read'),

    # ── Messages ─────────────────────────────────────────────────────────────
    path('inbox/',                      views.inbox,              name='inbox'),
    path('thread/<int:pk>/',            views.thread_detail,      name='thread'),
    path('thread/<int:pk>/send/',       views.send_message,       name='send_message'),
    path('thread/start/<int:reservation_pk>/', views.start_thread, name='start_thread'),
]
