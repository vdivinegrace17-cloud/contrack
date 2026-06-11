from django.contrib import admin
from .models import Notification, MessageThread, Message


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ('recipient', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter   = ('notification_type', 'is_read')
    search_fields = ('recipient__username', 'title')


class MessageInline(admin.TabularInline):
    model  = Message
    extra  = 0
    fields = ('sender', 'content', 'sent_at', 'is_read')
    readonly_fields = ('sent_at',)


@admin.register(MessageThread)
class MessageThreadAdmin(admin.ModelAdmin):
    list_display  = ('organizer', 'merchant', 'reservation', 'created_at')
    search_fields = ('organizer__org_name', 'merchant__business_name')
    inlines       = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display  = ('thread', 'sender', 'sent_at', 'is_read')
    list_filter   = ('is_read',)
    search_fields = ('sender__username', 'content')
