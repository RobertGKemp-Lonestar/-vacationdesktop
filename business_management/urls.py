from django.urls import path
from . import views

urlpatterns = [
    # CRM Dashboard
    path('', views.crm_dashboard_view, name='crm_dashboard'),
    
    # Client Management
    path('clients/', views.client_list_view, name='client_list'),
    path('clients/new/', views.client_create_view, name='client_create'),
    path('clients/<uuid:client_id>/', views.client_detail_view, name='client_detail'),
    path('clients/<uuid:client_id>/edit/', views.client_edit_view, name='client_edit'),
    path('clients/<uuid:client_id>/email/', views.send_client_email_view, name='send_client_email'),
    path('clients/<uuid:client_id>/communications/', views.client_communications_view, name='client_communications'),
    
    # Trip Management
    path('trips/', views.trip_list_view, name='trip_list'),
    path('trips/create/', views.trip_create_view, name='trip_create'),
    path('trips/<uuid:trip_id>/', views.trip_detail_view, name='trip_detail'),
    path('trips/<uuid:trip_id>/edit/', views.trip_edit_view, name='trip_edit'),
    path('trips/<uuid:trip_id>/confirm/', views.trip_confirm_view, name='trip_confirm'),
    path('trips/<uuid:trip_id>/itinerary/', views.trip_itinerary_view, name='trip_itinerary'),
    
    # Invoice Management  
    path('invoices/', views.invoice_list_view, name='invoice_list'),
    path('invoices/create/', views.invoice_create_view, name='invoice_create'),
    path('invoices/<uuid:invoice_id>/', views.invoice_detail_view, name='invoice_detail'),
    path('invoices/<uuid:invoice_id>/edit/', views.invoice_edit_view, name='invoice_edit'),
    path('invoices/<uuid:invoice_id>/send/', views.invoice_send_view, name='invoice_send'),
    path('invoices/<uuid:invoice_id>/delete/', views.invoice_delete_view, name='invoice_delete'),
]