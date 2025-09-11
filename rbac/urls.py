from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('profile/password/', views.password_change_view, name='password_change'),
    path('tenant/settings/', views.tenant_settings_view, name='tenant_settings'),
    
    # Password reset URLs
    path('password-reset/', views.password_reset_request_view, name='password_reset'),
    path('password-reset/done/', views.password_reset_done_view, name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', views.password_reset_confirm_view, name='password_reset_confirm'),
    path('password-reset/complete/', views.password_reset_complete_view, name='password_reset_complete'),
    
    # User management URLs
    path('users/', views.user_list_view, name='user_list'),
    path('users/add/', views.add_user_view, name='add_user'),
    path('users/<uuid:user_id>/edit/', views.edit_user_view, name='edit_user'),
    path('users/<uuid:user_id>/change-password/', views.change_user_password_view, name='change_user_password'),
    
    # Client support ticket URLs
    path('support/submit/', views.client_submit_ticket_view, name='client_submit_ticket'),
    path('support/my-tickets/', views.client_my_tickets_view, name='client_my_tickets'),
    path('support/tickets/<uuid:ticket_id>/', views.client_ticket_detail_view, name='client_ticket_detail'),
    
    # Staff dashboard and ticket management URLs
    path('staff/', views.staff_dashboard_view, name='staff_dashboard'),
    path('staff/tickets/', views.ticket_list_view, name='ticket_list'),
    path('staff/tickets/create/', views.create_ticket_view, name='create_ticket'),
    path('staff/tickets/<uuid:ticket_id>/', views.ticket_detail_view, name='ticket_detail'),
    path('staff/clients/', views.staff_client_management_view, name='staff_client_management'),
    path('staff/clients/<uuid:tenant_id>/create-user/', views.create_client_user_view, name='create_client_user'),
    
    # AJAX endpoints
    path('ajax/get-tenant-users/', views.get_tenant_users_ajax, name='get_tenant_users_ajax'),
    
    # Impersonation URLs
    path('impersonate/tenant/<uuid:tenant_id>/users/', views.impersonate_tenant_users, name='impersonate_tenant_users'),
    path('impersonate/start/<uuid:user_id>/', views.start_impersonation, name='start_impersonation'),
    path('impersonate/stop/', views.stop_impersonation, name='stop_impersonation'),
]