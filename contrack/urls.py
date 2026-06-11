from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django admin (superuser / organizer staff access)
    path('django-admin/', admin.site.urls),

    # Public auth routes (/, /merchant/login/, /merchant/register/, /organizer/login/)
    path('', include('apps.accounts.urls', namespace='accounts')),

    # Organizer portal — all views protected by @organizer_required
    path('organizer/', include('contrack.organizer_urls', namespace='organizer')),

    # Merchant portal — all views protected by @merchant_required
    path('merchant/', include('contrack.merchant_urls', namespace='merchant')),

    # Public event browsing (accessible without login)
    path('events/', include('apps.events.urls', namespace='events')),

    # Notifications (login required at view level)
    path('notifications/', include('apps.notifications.urls', namespace='notifications')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
