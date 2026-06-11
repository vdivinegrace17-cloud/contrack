from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Landing page
    path('', views.landing_view, name='landing'),

    # Merchant auth
    path('merchant/login/',    views.merchant_login_view,   name='merchant_login'),
    path('merchant/register/', views.merchant_register_view, name='merchant_register'),

    # Organizer auth (no public register)
    path('organizer/login/', views.organizer_login_view, name='organizer_login'),

    # Logout
    path('logout/', views.logout_view, name='logout'),

    # Dashboard routing (redirects to role-specific portal)
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),

    # Password reset
    path('password/reset/',
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/emails/password_reset_email.html',
             subject_template_name='accounts/emails/password_reset_subject.txt',
         ),
         name='password_reset'),

    path('password/reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html',
         ),
         name='password_reset_done'),

    path('password/reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
         ),
         name='password_reset_confirm'),

    path('password/reset/complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html',
         ),
         name='password_reset_complete'),
]
