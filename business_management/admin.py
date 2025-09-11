from django.contrib import admin
from .models import (
    Client, ClientCommunication, ClientNote, ClientDocument,
    Trip, TripItinerary, TripParticipant, TripCommunication,
    Invoice, InvoiceLineItem, Payment, PaymentSchedule
)


# ============================================================================
# CRM ADMIN
# ============================================================================

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'phone', 'tenant', 'is_active', 'vip_status', 'created_at']
    list_filter = ['tenant', 'is_active', 'vip_status', 'lead_source', 'preferred_communication']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('tenant', 'created_by', 'first_name', 'last_name', 'email', 'phone')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'country', 'postal_code'),
            'classes': ('collapse',)
        }),
        ('Travel Preferences', {
            'fields': ('preferred_communication', 'budget_range_min', 'budget_range_max', 
                      'preferred_destinations', 'travel_style', 'special_needs'),
            'classes': ('collapse',)
        }),
        ('Business Information', {
            'fields': ('lead_source', 'is_active', 'vip_status', 'last_contact_date')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ClientCommunication)
class ClientCommunicationAdmin(admin.ModelAdmin):
    list_display = ['client', 'communication_type', 'direction', 'subject', 'created_at']
    list_filter = ['communication_type', 'direction', 'created_at']
    search_fields = ['client__first_name', 'client__last_name', 'subject', 'content']
    readonly_fields = ['created_at']


@admin.register(ClientNote)
class ClientNoteAdmin(admin.ModelAdmin):
    list_display = ['client', 'note_type', 'title', 'is_important', 'created_at']
    list_filter = ['note_type', 'is_important', 'created_at']
    search_fields = ['client__first_name', 'client__last_name', 'title', 'content']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ClientDocument)
class ClientDocumentAdmin(admin.ModelAdmin):
    list_display = ['client', 'document_type', 'title', 'expiry_date', 'is_verified', 'created_at']
    list_filter = ['document_type', 'is_verified', 'created_at']
    search_fields = ['client__first_name', 'client__last_name', 'title']
    readonly_fields = ['created_at', 'file_size']


# ============================================================================
# TRIP ADMIN
# ============================================================================

class TripItineraryInline(admin.TabularInline):
    model = TripItinerary
    extra = 1
    ordering = ['day_number']


class TripParticipantInline(admin.TabularInline):
    model = TripParticipant
    extra = 1


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ['trip_name', 'client', 'status', 'departure_date', 'return_date', 'total_amount', 'created_at']
    list_filter = ['status', 'trip_type', 'departure_date', 'created_at']
    search_fields = ['trip_name', 'client__first_name', 'client__last_name', 'destination']
    readonly_fields = ['created_at', 'updated_at', 'duration_days', 'is_upcoming']
    inlines = [TripParticipantInline, TripItineraryInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('client', 'created_by', 'trip_name', 'trip_type', 'status')
        }),
        ('Dates & Locations', {
            'fields': ('departure_date', 'return_date', 'departure_location', 'destination', 'destinations')
        }),
        ('Pricing', {
            'fields': ('estimated_cost', 'quoted_price', 'total_amount')
        }),
        ('Details', {
            'fields': ('number_of_travelers', 'special_requests', 'internal_notes')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'duration_days', 'is_upcoming'),
            'classes': ('collapse',)
        })
    )


@admin.register(TripCommunication)
class TripCommunicationAdmin(admin.ModelAdmin):
    list_display = ['trip', 'communication_type', 'subject', 'email_delivered', 'sent_at']
    list_filter = ['communication_type', 'email_delivered', 'sent_at']
    search_fields = ['trip__trip_name', 'subject', 'content']


# ============================================================================
# INVOICE ADMIN
# ============================================================================

class InvoiceLineItemInline(admin.TabularInline):
    model = InvoiceLineItem
    extra = 1


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ['created_at']


class PaymentScheduleInline(admin.TabularInline):
    model = PaymentSchedule
    extra = 1


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'client', 'trip', 'status', 'total_amount', 'paid_amount', 'balance_due', 'due_date']
    list_filter = ['status', 'invoice_date', 'due_date']
    search_fields = ['invoice_number', 'client__first_name', 'client__last_name', 'trip__trip_name']
    readonly_fields = ['created_at', 'updated_at', 'balance_due', 'is_overdue']
    inlines = [InvoiceLineItemInline, PaymentInline, PaymentScheduleInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('client', 'trip', 'created_by', 'invoice_number', 'status')
        }),
        ('Amounts', {
            'fields': ('subtotal', 'tax_amount', 'total_amount', 'paid_amount', 'balance_due')
        }),
        ('Dates', {
            'fields': ('invoice_date', 'due_date', 'is_overdue')
        }),
        ('Content', {
            'fields': ('notes', 'terms'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'amount', 'payment_method', 'payment_date', 'reference_number']
    list_filter = ['payment_method', 'payment_date']
    search_fields = ['invoice__invoice_number', 'reference_number']
    readonly_fields = ['created_at']