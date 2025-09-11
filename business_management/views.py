from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import (
    Client, ClientCommunication, ClientNote, ClientDocument,
    Trip, TripLineItem, TripItinerary, TripParticipant, TripCommunication,
    Invoice, InvoiceLineItem, Payment, PaymentSchedule
)
from .email_service import TenantEmailService


# ============================================================================
# CLIENT MANAGEMENT VIEWS
# ============================================================================

@login_required
def client_list_view(request):
    """List all clients for the current tenant with search and filtering"""
    # Only show clients for current tenant
    clients = Client.objects.filter(tenant=request.user.tenant)
    
    # Search functionality
    search = request.GET.get('search', '')
    if search:
        clients = clients.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search)
        )
    
    # Filter by VIP status
    vip_filter = request.GET.get('vip', '')
    if vip_filter:
        clients = clients.filter(vip_status=vip_filter)
    
    # Filter by lead source
    source_filter = request.GET.get('source', '')
    if source_filter:
        clients = clients.filter(lead_source=source_filter)
    
    # Filter by active status
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        clients = clients.filter(is_active=True)
    elif status_filter == 'inactive':
        clients = clients.filter(is_active=False)
    
    # Annotate with trip and invoice counts
    clients = clients.annotate(
        trip_count=Count('trips'),
        total_spent=Sum('trips__total_amount')
    ).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(clients, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'clients': page_obj,
        'page_obj': page_obj,
        'search': search,
        'vip_filter': vip_filter,
        'source_filter': source_filter,
        'status_filter': status_filter,
        'vip_choices': Client.VIP_STATUS_CHOICES,
        'source_choices': Client.LEAD_SOURCE_CHOICES,
        'total_clients': clients.count(),
        'active_clients': Client.objects.filter(tenant=request.user.tenant, is_active=True).count(),
        'vip_clients': Client.objects.filter(tenant=request.user.tenant, vip_status__in=['VIP', 'PREMIUM']).count(),
    }
    
    return render(request, 'business_management/client_list.html', context)


@login_required
def client_detail_view(request, client_id):
    """Detailed view of a specific client"""
    client = get_object_or_404(Client, id=client_id, tenant=request.user.tenant)
    
    # Get client's trips
    trips = client.trips.all().order_by('-departure_date')
    
    # Get client's invoices
    invoices = Invoice.objects.filter(client=client).order_by('-invoice_date')
    
    # Get recent communications
    recent_communications = client.communications.all().order_by('-created_at')[:10]
    
    # Get client notes
    notes = client.notes.all().order_by('-created_at')[:5]
    
    # Get client documents
    documents = client.documents.all().order_by('-created_at')
    
    # Calculate summary statistics
    total_trips = trips.count()
    total_spent = trips.aggregate(total=Sum('total_amount'))['total'] or 0
    pending_balance = invoices.filter(status__in=['SENT', 'VIEWED']).aggregate(
        total=Sum('total_amount') - Sum('paid_amount')
    )['total'] or 0
    
    context = {
        'client': client,
        'trips': trips[:5],  # Show last 5 trips
        'invoices': invoices[:5],  # Show last 5 invoices
        'recent_communications': recent_communications,
        'notes': notes,
        'documents': documents,
        'total_trips': total_trips,
        'total_spent': total_spent,
        'pending_balance': pending_balance,
        'upcoming_trips': trips.filter(departure_date__gte=timezone.now().date())[:3],
    }
    
    return render(request, 'business_management/client_detail.html', context)


@login_required
def client_create_view(request):
    """Create a new client"""
    if request.method == 'POST':
        # Simple form handling - we'll create a proper form class later
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        
        if first_name and last_name and email:
            client = Client.objects.create(
                tenant=request.user.tenant,
                created_by=request.user,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                lead_source=request.POST.get('lead_source', 'OTHER'),
                preferred_communication=request.POST.get('preferred_communication', 'EMAIL'),
                vip_status=request.POST.get('vip_status', 'REGULAR'),
            )
            
            messages.success(request, f'Client {client.full_name} created successfully!')
            return redirect('client_detail', client_id=client.id)
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    context = {
        'title': 'Add New Client',
        'action': 'Create',
        'lead_source_choices': Client.LEAD_SOURCE_CHOICES,
        'communication_choices': Client.COMMUNICATION_PREFERENCES,
    }
    
    return render(request, 'business_management/client_form.html', context)


@login_required
def client_edit_view(request, client_id):
    """Edit an existing client"""
    client = get_object_or_404(Client, id=client_id, tenant=request.user.tenant)
    
    if request.method == 'POST':
        # Update client fields
        client.first_name = request.POST.get('first_name', client.first_name)
        client.last_name = request.POST.get('last_name', client.last_name)
        client.email = request.POST.get('email', client.email)
        client.phone = request.POST.get('phone', client.phone)
        client.lead_source = request.POST.get('lead_source', client.lead_source)
        client.preferred_communication = request.POST.get('preferred_communication', client.preferred_communication)
        client.vip_status = request.POST.get('vip_status', client.vip_status)
        client.save()
        
        messages.success(request, f'Client {client.full_name} updated successfully!')
        return redirect('client_detail', client_id=client.id)
    
    context = {
        'client': client,
        'title': f'Edit {client.full_name}',
        'action': 'Update',
        'lead_source_choices': Client.LEAD_SOURCE_CHOICES,
        'communication_choices': Client.COMMUNICATION_PREFERENCES,
    }
    
    return render(request, 'business_management/client_form.html', context)


# ============================================================================
# TRIP MANAGEMENT VIEWS
# ============================================================================

@login_required
def trip_list_view(request):
    """List all trips for the current tenant"""
    trips = Trip.objects.filter(client__tenant=request.user.tenant)
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        trips = trips.filter(status=status_filter)
    
    # Filter by date range
    date_filter = request.GET.get('date_filter', '')
    if date_filter == 'upcoming':
        trips = trips.filter(departure_date__gte=timezone.now().date())
    elif date_filter == 'past':
        trips = trips.filter(return_date__lt=timezone.now().date())
    elif date_filter == 'current':
        today = timezone.now().date()
        trips = trips.filter(departure_date__lte=today, return_date__gte=today)
    
    # Search functionality
    search = request.GET.get('search', '')
    if search:
        trips = trips.filter(
            Q(trip_name__icontains=search) |
            Q(client__first_name__icontains=search) |
            Q(client__last_name__icontains=search) |
            Q(destination__icontains=search)
        )
    
    trips = trips.select_related('client').annotate(
        participant_count=Count('participants')
    ).order_by('-departure_date')
    
    # Pagination
    paginator = Paginator(trips, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate additional metrics
    active_trips = trips.filter(status='IN_PROGRESS').count()
    
    context = {
        'trips': page_obj,
        'page_obj': page_obj,
        'search': search,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'status_choices': Trip.STATUS_CHOICES,
        'total_trips': trips.count(),
        'upcoming_trips': Trip.objects.filter(
            client__tenant=request.user.tenant, 
            departure_date__gte=timezone.now().date()
        ).count(),
        'active_trips': active_trips,
    }
    
    return render(request, 'business_management/trip_list.html', context)


@login_required
def trip_detail_view(request, trip_id):
    """Detailed view of a specific trip"""
    trip = get_object_or_404(Trip, id=trip_id, client__tenant=request.user.tenant)
    
    if request.method == 'POST':
        # Handle AJAX requests for line item management
        action = request.POST.get('action')
        
        if action == 'add_line_item':
            try:
                item_type = request.POST.get('item_type')
                description = request.POST.get('description')
                supplier = request.POST.get('supplier', '')
                quantity = int(request.POST.get('quantity', 1))
                unit_price = float(request.POST.get('unit_price', 0))
                total_price = float(request.POST.get('total_price', 0))
                service_date = request.POST.get('service_date') or None
                confirmation_number = request.POST.get('confirmation_number', '')
                is_confirmed = request.POST.get('is_confirmed') == 'on'
                is_paid = request.POST.get('is_paid') == 'on'
                
                TripLineItem.objects.create(
                    trip=trip,
                    item_type=item_type,
                    description=description,
                    supplier=supplier,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price,
                    service_date=service_date,
                    confirmation_number=confirmation_number,
                    is_confirmed=is_confirmed,
                    is_paid=is_paid,
                )
                
                return JsonResponse({'success': True, 'message': 'Line item added successfully!'})
                
            except Exception as e:
                return JsonResponse({'success': False, 'message': f'Error adding line item: {str(e)}'})
        
        elif action == 'delete_line_item':
            try:
                item_id = request.POST.get('line_item_id')
                item = TripLineItem.objects.get(id=item_id, trip=trip)
                item.delete()
                return JsonResponse({'success': True, 'message': 'Line item deleted successfully!'})
            except TripLineItem.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Line item not found.'})
        
        elif action == 'send_trip_to_client':
            try:
                custom_message = request.POST.get('custom_message', '')
                include_itinerary = request.POST.get('include_itinerary') == 'on'
                include_line_items = request.POST.get('include_line_items') == 'on'
                
                # Get email service for tenant
                email_service = TenantEmailService(tenant=request.user.tenant)
                
                # Prepare context for email
                context_data = {
                    'trip': trip,
                    'message': custom_message,
                }
                
                if include_itinerary:
                    context_data['itinerary_days'] = trip.itinerary_days.all().order_by('day_number')
                
                if include_line_items:
                    context_data['line_items'] = trip.line_items.all().order_by('item_type', 'service_date')
                    context_data['line_items_total'] = sum(item.total_price for item in context_data['line_items'])
                
                # Send trip email using existing itinerary template
                success, communication = email_service.send_client_email(
                    client=trip.client,
                    subject=f'Your Trip Information: {trip.trip_name} - {trip.destination}',
                    template_name='itinerary',
                    context=context_data,
                    sender_name=request.user.get_full_name() or request.user.username
                )
                
                if success:
                    return JsonResponse({
                        'success': True, 
                        'message': f'Trip information sent successfully to {trip.client.full_name}!'
                    })
                else:
                    return JsonResponse({
                        'success': False, 
                        'message': 'Failed to send trip information. Please try again.'
                    })
                    
            except Exception as e:
                return JsonResponse({
                    'success': False, 
                    'message': f'Error sending trip information: {str(e)}'
                })
        
        elif action == 'push_to_invoice':
            try:
                line_item_id = request.POST.get('line_item_id')
                line_item = TripLineItem.objects.get(id=line_item_id, trip=trip)
                
                # Get or create an invoice for this trip
                invoice, created = Invoice.objects.get_or_create(
                    trip=trip,
                    client=trip.client,
                    defaults={
                        'created_by': request.user,
                        'invoice_number': f'INV-{trip.id.hex[:8].upper()}',
                        'subtotal': 0,
                        'total_amount': 0,
                        'due_date': timezone.now().date() + timedelta(days=30),
                        'notes': f'Invoice for trip: {trip.trip_name}',
                    }
                )
                
                # Check if this line item is already on the invoice
                existing_invoice_item = InvoiceLineItem.objects.filter(
                    invoice=invoice,
                    description=line_item.description,
                    unit_price=line_item.unit_price
                ).first()
                
                if existing_invoice_item:
                    return JsonResponse({
                        'success': False, 
                        'message': 'This item is already on the invoice.'
                    })
                
                # Create invoice line item
                InvoiceLineItem.objects.create(
                    invoice=invoice,
                    description=f"{line_item.get_item_type_display()}: {line_item.description}",
                    quantity=line_item.quantity,
                    unit_price=line_item.unit_price,
                    total_price=line_item.total_price,
                )
                
                # Update invoice totals
                invoice.subtotal = sum(item.total_price for item in invoice.line_items.all())
                invoice.total_amount = invoice.subtotal + invoice.tax_amount
                invoice.save()
                
                action_text = "created" if created else "updated"
                return JsonResponse({
                    'success': True,
                    'message': f'Item pushed to invoice successfully! Invoice {action_text}: {invoice.invoice_number}'
                })
                
            except TripLineItem.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Line item not found.'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': f'Error pushing to invoice: {str(e)}'})
        
        elif action == 'push_all_to_invoice':
            try:
                line_items = trip.line_items.all()
                
                if not line_items.exists():
                    return JsonResponse({'success': False, 'message': 'No line items to push to invoice.'})
                
                # Get or create an invoice for this trip
                invoice, created = Invoice.objects.get_or_create(
                    trip=trip,
                    client=trip.client,
                    defaults={
                        'created_by': request.user,
                        'invoice_number': f'INV-{trip.id.hex[:8].upper()}',
                        'subtotal': 0,
                        'total_amount': 0,
                        'due_date': timezone.now().date() + timedelta(days=30),
                        'notes': f'Invoice for trip: {trip.trip_name}',
                    }
                )
                
                added_count = 0
                skipped_count = 0
                
                for line_item in line_items:
                    # Check if this line item is already on the invoice
                    existing_invoice_item = InvoiceLineItem.objects.filter(
                        invoice=invoice,
                        description__icontains=line_item.description,
                        unit_price=line_item.unit_price
                    ).first()
                    
                    if existing_invoice_item:
                        skipped_count += 1
                        continue
                    
                    # Create invoice line item
                    InvoiceLineItem.objects.create(
                        invoice=invoice,
                        description=f"{line_item.get_item_type_display()}: {line_item.description}",
                        quantity=line_item.quantity,
                        unit_price=line_item.unit_price,
                        total_price=line_item.total_price,
                    )
                    added_count += 1
                
                # Update invoice totals
                invoice.subtotal = sum(item.total_price for item in invoice.line_items.all())
                invoice.total_amount = invoice.subtotal + invoice.tax_amount
                invoice.save()
                
                if added_count > 0:
                    action_text = "created" if created else "updated"
                    message = f'{added_count} items pushed to invoice successfully! Invoice {action_text}: {invoice.invoice_number}'
                    if skipped_count > 0:
                        message += f' ({skipped_count} items were already on the invoice)'
                    return JsonResponse({'success': True, 'message': message})
                else:
                    return JsonResponse({'success': False, 'message': 'All items are already on the invoice.'})
                
            except Exception as e:
                return JsonResponse({'success': False, 'message': f'Error pushing items to invoice: {str(e)}'})
    
    # Get trip components
    participants = trip.participants.all()
    itinerary_days = trip.itinerary_days.all().order_by('day_number')
    line_items = trip.line_items.all().order_by('item_type', 'service_date')
    line_items_total = sum(item.total_price for item in line_items)
    invoices = trip.invoices.all().order_by('-invoice_date')
    communications = trip.communications.all().order_by('-sent_at')
    
    context = {
        'trip': trip,
        'participants': participants,
        'itinerary_days': itinerary_days,
        'line_items': line_items,
        'line_items_total': line_items_total,
        'invoices': invoices,
        'communications': communications,
        'days_until_departure': (trip.departure_date - timezone.now().date()).days if trip.departure_date else None,
    }
    
    return render(request, 'business_management/trip_detail.html', context)


# ============================================================================
# INVOICE MANAGEMENT VIEWS  
# ============================================================================

@login_required
def invoice_list_view(request):
    """List all invoices for the current tenant"""
    invoices = Invoice.objects.filter(client__tenant=request.user.tenant)
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        invoices = invoices.filter(status=status_filter)
    
    # Filter by overdue
    overdue_filter = request.GET.get('overdue', '')
    if overdue_filter == 'yes':
        invoices = invoices.filter(due_date__lt=timezone.now().date(), status__in=['SENT', 'VIEWED'])
    
    # Search functionality  
    search = request.GET.get('search', '')
    if search:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search) |
            Q(client__first_name__icontains=search) |
            Q(client__last_name__icontains=search)
        )
    
    invoices = invoices.select_related('client', 'trip').order_by('-invoice_date')
    
    # Pagination
    paginator = Paginator(invoices, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate summary statistics
    total_outstanding = invoices.filter(status__in=['SENT', 'VIEWED']).aggregate(
        total=Sum('total_amount') - Sum('paid_amount')
    )['total'] or 0
    
    overdue_amount = invoices.filter(
        due_date__lt=timezone.now().date(), 
        status__in=['SENT', 'VIEWED']
    ).aggregate(
        total=Sum('total_amount') - Sum('paid_amount')
    )['total'] or 0
    
    context = {
        'invoices': page_obj,
        'page_obj': page_obj,
        'search': search,
        'status_filter': status_filter,
        'overdue_filter': overdue_filter,
        'status_choices': Invoice.STATUS_CHOICES,
        'total_invoices': invoices.count(),
        'total_outstanding': total_outstanding,
        'overdue_amount': overdue_amount,
    }
    
    return render(request, 'business_management/invoice_list.html', context)


@login_required
def invoice_detail_view(request, invoice_id):
    """Detailed view of a specific invoice"""
    invoice = get_object_or_404(Invoice, id=invoice_id, client__tenant=request.user.tenant)
    
    # Get invoice components
    line_items = invoice.line_items.all()
    payments = invoice.payments.all().order_by('-payment_date')
    payment_schedule = invoice.payment_schedule.all().order_by('due_date')
    
    context = {
        'invoice': invoice,
        'line_items': line_items,
        'payments': payments,
        'payment_schedule': payment_schedule,
        'days_until_due': (invoice.due_date - timezone.now().date()).days if invoice.due_date else None,
    }
    
    return render(request, 'business_management/invoice_detail.html', context)


# ============================================================================
# DASHBOARD AND OVERVIEW VIEWS
# ============================================================================

@login_required
def crm_dashboard_view(request):
    """Main CRM dashboard for travel advisors"""
    tenant = request.user.tenant
    
    # Get key metrics
    total_clients = Client.objects.filter(tenant=tenant).count()
    active_clients = Client.objects.filter(tenant=tenant, is_active=True).count()
    vip_clients = Client.objects.filter(tenant=tenant, vip_status__in=['VIP', 'PREMIUM']).count()
    
    # Trip metrics
    total_trips = Trip.objects.filter(client__tenant=tenant).count()
    upcoming_trips = Trip.objects.filter(
        client__tenant=tenant, 
        departure_date__gte=timezone.now().date()
    ).count()
    
    # Financial metrics
    total_revenue = Trip.objects.filter(client__tenant=tenant).aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    pending_payments = Invoice.objects.filter(
        client__tenant=tenant, 
        status__in=['SENT', 'VIEWED']
    ).aggregate(
        total=Sum('total_amount') - Sum('paid_amount')
    )['total'] or 0
    
    # Recent activity
    recent_clients = Client.objects.filter(tenant=tenant).order_by('-created_at')[:5]
    upcoming_departures = Trip.objects.filter(
        client__tenant=tenant,
        departure_date__gte=timezone.now().date()
    ).order_by('departure_date')[:5]
    
    overdue_invoices = Invoice.objects.filter(
        client__tenant=tenant,
        due_date__lt=timezone.now().date(),
        status__in=['SENT', 'VIEWED']
    ).order_by('due_date')[:5]
    
    context = {
        'total_clients': total_clients,
        'active_clients': active_clients,
        'vip_clients': vip_clients,
        'total_trips': total_trips,
        'upcoming_trips': upcoming_trips,
        'total_revenue': total_revenue,
        'pending_payments': pending_payments,
        'recent_clients': recent_clients,
        'upcoming_departures': upcoming_departures,
        'overdue_invoices': overdue_invoices,
    }
    
    return render(request, 'business_management/crm_dashboard.html', context)


# ============================================================================
# COMMUNICATION VIEWS
# ============================================================================

@login_required
def send_client_email_view(request, client_id):
    """Send email to a specific client"""
    client = get_object_or_404(Client, id=client_id, tenant=request.user.tenant)
    
    if request.method == 'POST':
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        template_name = request.POST.get('template', 'generic')
        
        if subject and message:
            # Get email service for tenant
            email_service = TenantEmailService(tenant=request.user.tenant)
            
            # Send email
            success, communication = email_service.send_client_email(
                client=client,
                subject=subject,
                template_name=template_name,
                context={'message': message},
                sender_name=request.user.get_full_name() or request.user.username
            )
            
            if success:
                messages.success(request, f'Email sent to {client.full_name} successfully!')
            else:
                messages.error(request, 'Failed to send email. Please try again.')
            
            return redirect('client_detail', client_id=client.id)
    
    context = {
        'client': client,
        'email_templates': [
            ('generic', 'Generic Email'),
            ('trip_update', 'Trip Update'),
            ('payment_reminder', 'Payment Reminder'),
            ('welcome', 'Welcome Message'),
        ]
    }
    
    return render(request, 'business_management/send_email.html', context)


@login_required
def trip_create_view(request):
    """Create a new trip"""
    if request.method == 'POST':
        # Get client
        client_id = request.POST.get('client_id')
        client = get_object_or_404(Client, id=client_id, tenant=request.user.tenant)
        
        # Basic trip data
        trip_name = request.POST.get('trip_name')
        trip_type = request.POST.get('trip_type', 'CRUISE')
        custom_trip_type = request.POST.get('custom_trip_type', '')
        destination = request.POST.get('destination')
        departure_date = request.POST.get('departure_date')
        return_date = request.POST.get('return_date')
        special_requests = request.POST.get('special_requests', '')
        total_amount = request.POST.get('total_amount')
        budget_range_min = request.POST.get('budget_range_min')
        budget_range_max = request.POST.get('budget_range_max')
        number_of_travelers = request.POST.get('number_of_travelers', '1')
        description = request.POST.get('description', '')
        
        if trip_name and destination and departure_date and return_date:
            trip = Trip.objects.create(
                client=client,
                created_by=request.user,
                trip_name=trip_name,
                trip_type=trip_type,
                custom_trip_type=custom_trip_type if trip_type == 'OTHER' else '',
                destination=destination,
                departure_date=departure_date,
                return_date=return_date,
                special_requests=special_requests,
                total_amount=float(total_amount) if total_amount else None,
                budget_range_min=float(budget_range_min) if budget_range_min else None,
                budget_range_max=float(budget_range_max) if budget_range_max else None,
                number_of_travelers=int(number_of_travelers) if number_of_travelers else 1,
                description=description,
                status='PLANNING',
            )
            
            messages.success(request, f'Trip "{trip.trip_name}" created successfully!')
            return redirect('trip_detail', trip_id=trip.id)
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    # Get clients for dropdown
    clients = Client.objects.filter(tenant=request.user.tenant, is_active=True).order_by('first_name', 'last_name')
    
    context = {
        'clients': clients,
        'title': 'Create New Trip',
        'action': 'Create',
        'trip_type_choices': Trip.TRIP_TYPES,
        'status_choices': Trip.STATUS_CHOICES,
    }
    
    return render(request, 'business_management/trip_form.html', context)


@login_required  
def trip_edit_view(request, trip_id):
    """Edit an existing trip"""
    trip = get_object_or_404(Trip, id=trip_id, client__tenant=request.user.tenant)
    
    if request.method == 'POST':
        # Update trip fields
        trip.trip_name = request.POST.get('trip_name', trip.trip_name)
        trip.trip_type = request.POST.get('trip_type', trip.trip_type)
        trip.custom_trip_type = request.POST.get('custom_trip_type', '') if request.POST.get('trip_type') == 'OTHER' else ''
        trip.destination = request.POST.get('destination', trip.destination)
        trip.departure_date = request.POST.get('departure_date', trip.departure_date)
        trip.return_date = request.POST.get('return_date', trip.return_date)
        trip.special_requests = request.POST.get('special_requests', trip.special_requests)
        
        # Handle status changes with special logic for FINALIZED
        new_status = request.POST.get('status', trip.status)
        if new_status == 'FINALIZED' and trip.status != 'FINALIZED':
            # Trip is being finalized - check if auto-create invoice is requested
            auto_create_invoice = request.POST.get('auto_create_invoice') == 'on'
            if auto_create_invoice:
                # Create invoice automatically
                from datetime import datetime
                invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{Invoice.objects.count() + 1:04d}"
                Invoice.objects.create(
                    client=trip.client,
                    trip=trip,
                    created_by=request.user,
                    invoice_number=invoice_number,
                    invoice_date=timezone.now().date(),
                    due_date=None,  # Will be set in invoice editing
                    subtotal=trip.total_amount or 0,
                    tax_amount=0,
                    total_amount=trip.total_amount or 0,
                    paid_amount=0,
                    status='DRAFT',
                    notes=f'Auto-generated invoice for {trip.trip_name}',
                )
                messages.success(request, f'Trip finalized and invoice {invoice_number} created!')
        
        trip.status = new_status
        
        total_amount = request.POST.get('total_amount')
        if total_amount and total_amount.strip():
            trip.total_amount = float(total_amount)
        # If total_amount is empty, keep the existing value
        
        # Update budget range
        budget_range_min = request.POST.get('budget_range_min')
        budget_range_max = request.POST.get('budget_range_max')
        if budget_range_min and budget_range_min.strip():
            trip.budget_range_min = float(budget_range_min)
        elif budget_range_min == '':  # Explicitly cleared
            trip.budget_range_min = None
            
        if budget_range_max and budget_range_max.strip():
            trip.budget_range_max = float(budget_range_max)
        elif budget_range_max == '':  # Explicitly cleared
            trip.budget_range_max = None
        
        # Update number of travelers and description
        number_of_travelers = request.POST.get('number_of_travelers')
        if number_of_travelers and number_of_travelers.strip():
            trip.number_of_travelers = int(number_of_travelers)
        
        trip.description = request.POST.get('description', trip.description)
        
        trip.save()
        
        messages.success(request, f'Trip "{trip.trip_name}" updated successfully!')
        return redirect('trip_detail', trip_id=trip.id)
    
    # Get clients for dropdown (in case they want to change client)
    clients = Client.objects.filter(tenant=request.user.tenant, is_active=True).order_by('first_name', 'last_name')
    
    context = {
        'trip': trip,
        'clients': clients,
        'title': f'Edit {trip.trip_name}',
        'action': 'Update',
        'trip_type_choices': Trip.TRIP_TYPES,
        'status_choices': Trip.STATUS_CHOICES,
    }
    
    return render(request, 'business_management/trip_form.html', context)


@login_required
def trip_confirm_view(request, trip_id):
    """AJAX endpoint to confirm a trip"""
    if request.method == 'POST':
        trip = get_object_or_404(Trip, id=trip_id, client__tenant=request.user.tenant)
        
        if trip.status == 'DRAFT':
            trip.status = 'CONFIRMED'
            trip.save()
            
            return JsonResponse({'success': True, 'message': 'Trip confirmed successfully!'})
        else:
            return JsonResponse({'success': False, 'message': 'Trip is not in draft status.'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


@login_required
def trip_itinerary_view(request, trip_id):
    """Manage trip itinerary"""
    trip = get_object_or_404(Trip, id=trip_id, client__tenant=request.user.tenant)
    itinerary_days = trip.itinerary_days.all().order_by('day_number')
    
    if request.method == 'POST':
        # Handle AJAX requests for itinerary management
        action = request.POST.get('action')
        
        if action == 'add_day':
            day_number = request.POST.get('day_number')
            title = request.POST.get('title', '')
            description = request.POST.get('description', '')
            
            TripItinerary.objects.create(
                trip=trip,
                day_number=int(day_number),
                title=title,
                description=description,
            )
            
            return JsonResponse({'success': True, 'message': f'Day {day_number} added successfully!'})
        
        elif action == 'edit_day':
            day_id = request.POST.get('day_id')
            title = request.POST.get('title', '')
            description = request.POST.get('description', '')
            
            try:
                day = TripItinerary.objects.get(id=day_id, trip=trip)
                day.title = title
                day.description = description
                day.save()
                return JsonResponse({'success': True, 'message': 'Day updated successfully!'})
            except TripItinerary.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Day not found.'})
        
        elif action == 'delete_day':
            day_id = request.POST.get('day_id')
            
            try:
                day = TripItinerary.objects.get(id=day_id, trip=trip)
                day_number = day.day_number
                day.delete()
                
                # Renumber subsequent days
                subsequent_days = TripItinerary.objects.filter(
                    trip=trip, 
                    day_number__gt=day_number
                ).order_by('day_number')
                
                for i, day in enumerate(subsequent_days):
                    day.day_number = day_number + i
                    day.save()
                
                return JsonResponse({'success': True, 'message': 'Day deleted successfully!'})
            except TripItinerary.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Day not found.'})
        
        elif action == 'email_itinerary':
            include_pdf = request.POST.get('include_pdf') == 'on'
            custom_message = request.POST.get('custom_message', '')
            
            try:
                # Get email service for tenant
                email_service = TenantEmailService(tenant=request.user.tenant)
                
                # Send itinerary email
                success, communication = email_service.send_client_email(
                    client=trip.client,
                    subject=f'Your Itinerary: {trip.trip_name} - {trip.destination}',
                    template_name='itinerary',
                    context={
                        'trip': trip,
                        'itinerary_days': itinerary_days,
                        'message': custom_message,
                    },
                    sender_name=request.user.get_full_name() or request.user.username
                )
                
                if success:
                    return JsonResponse({
                        'success': True, 
                        'message': f'Itinerary sent successfully to {trip.client.full_name}!'
                    })
                else:
                    return JsonResponse({
                        'success': False, 
                        'message': 'Failed to send itinerary. Please try again.'
                    })
                    
            except Exception as e:
                return JsonResponse({
                    'success': False, 
                    'message': f'Error sending itinerary: {str(e)}'
                })
    
    context = {
        'trip': trip,
        'itinerary_days': itinerary_days,
    }
    
    return render(request, 'business_management/trip_itinerary.html', context)


# ============================================================================
# ADDITIONAL INVOICE MANAGEMENT VIEWS
# ============================================================================

@login_required
def invoice_create_view(request):
    """Create a new invoice"""
    if request.method == 'POST':
        # Get client and optional trip
        client_id = request.POST.get('client_id')
        client = get_object_or_404(Client, id=client_id, tenant=request.user.tenant)
        
        trip_id = request.POST.get('trip_id')
        trip = None
        if trip_id:
            trip = get_object_or_404(Trip, id=trip_id, client__tenant=request.user.tenant)
        
        # Invoice details
        due_date = request.POST.get('due_date')
        notes = request.POST.get('notes', '')
        
        # Generate invoice number (simple format)
        from datetime import datetime
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{Invoice.objects.count() + 1:04d}"
        
        # Calculate amounts (we'll implement line items in a future iteration)
        total_amount = float(request.POST.get('total_amount', '0'))
        subtotal = total_amount  # For now, subtotal equals total (no tax or discounts)
        
        invoice = Invoice.objects.create(
            client=client,
            trip=trip,
            created_by=request.user,
            invoice_number=invoice_number,
            invoice_date=timezone.now().date(),
            due_date=due_date if due_date else None,
            subtotal=subtotal,
            tax_amount=0,  # Default to 0 for now
            total_amount=total_amount,
            paid_amount=0,
            status='DRAFT',
            notes=notes,
        )
        
        messages.success(request, f'Invoice {invoice.invoice_number} created successfully!')
        return redirect('invoice_detail', invoice_id=invoice.id)
    
    # Get clients and trips for dropdowns
    clients = Client.objects.filter(tenant=request.user.tenant, is_active=True).order_by('first_name', 'last_name')
    trips = Trip.objects.filter(client__tenant=request.user.tenant).order_by('-departure_date')[:50]
    
    context = {
        'clients': clients,
        'trips': trips,
        'title': 'Create New Invoice',
        'action': 'Create',
    }
    
    return render(request, 'business_management/invoice_form.html', context)


@login_required
def invoice_edit_view(request, invoice_id):
    """Edit an existing invoice"""
    invoice = get_object_or_404(Invoice, id=invoice_id, client__tenant=request.user.tenant)
    
    if request.method == 'POST':
        # Update invoice fields
        invoice.due_date = request.POST.get('due_date') or None
        invoice.notes = request.POST.get('notes', invoice.notes)
        invoice.status = request.POST.get('status', invoice.status)
        
        total_amount = request.POST.get('total_amount')
        if total_amount:
            invoice.total_amount = float(total_amount)
            invoice.subtotal = float(total_amount)  # For now, subtotal equals total
        
        invoice.save()
        
        messages.success(request, f'Invoice {invoice.invoice_number} updated successfully!')
        return redirect('invoice_detail', invoice_id=invoice.id)
    
    # Get clients and trips for dropdowns
    clients = Client.objects.filter(tenant=request.user.tenant, is_active=True).order_by('first_name', 'last_name')
    trips = Trip.objects.filter(client__tenant=request.user.tenant).order_by('-departure_date')[:50]
    
    context = {
        'invoice': invoice,
        'clients': clients,
        'trips': trips,
        'title': f'Edit {invoice.invoice_number}',
        'action': 'Update',
        'status_choices': Invoice.STATUS_CHOICES,
    }
    
    return render(request, 'business_management/invoice_form.html', context)


@login_required
def invoice_send_view(request, invoice_id):
    """Send invoice to client via email"""
    invoice = get_object_or_404(Invoice, id=invoice_id, client__tenant=request.user.tenant)
    
    if request.method == 'POST':
        # Get email service for tenant
        email_service = TenantEmailService(tenant=request.user.tenant)
        
        # Send invoice email
        success, communication = email_service.send_client_email(
            client=invoice.client,
            subject=f'Invoice {invoice.invoice_number} - {invoice.total_amount}',
            template_name='invoice',
            context={
                'invoice': invoice,
                'message': f'Please find attached your invoice for ${invoice.total_amount}. Payment is due by {invoice.due_date}.'
            },
            sender_name=request.user.get_full_name() or request.user.username
        )
        
        if success:
            # Update invoice status
            if invoice.status == 'DRAFT':
                invoice.status = 'SENT'
                invoice.save()
            
            messages.success(request, f'Invoice {invoice.invoice_number} sent to {invoice.client.full_name}!')
        else:
            messages.error(request, 'Failed to send invoice. Please try again.')
        
        return redirect('invoice_detail', invoice_id=invoice.id)
    
    context = {
        'invoice': invoice,
    }
    
    return render(request, 'business_management/invoice_send.html', context)


@login_required
def invoice_delete_view(request, invoice_id):
    """Delete an invoice"""
    invoice = get_object_or_404(Invoice, id=invoice_id, client__tenant=request.user.tenant)
    
    if request.method == 'POST':
        invoice_number = invoice.invoice_number
        client_name = invoice.client.full_name
        
        # Only allow deletion of draft invoices or invoices that haven't been paid
        if invoice.status in ['DRAFT', 'SENT', 'VIEWED'] and invoice.paid_amount == 0:
            invoice.delete()
            messages.success(request, f'Invoice {invoice_number} for {client_name} has been deleted.')
            return redirect('invoice_list')
        else:
            messages.error(request, 'Cannot delete invoices that have been paid or are in an advanced status.')
            return redirect('invoice_detail', invoice_id=invoice.id)
    
    # For GET requests, return to invoice detail with error
    messages.error(request, 'Invalid request method.')
    return redirect('invoice_detail', invoice_id=invoice.id)


# ============================================================================
# CLIENT COMMUNICATION TRACKING VIEWS
# ============================================================================

@login_required
def client_communications_view(request, client_id):
    """View all communications with a specific client"""
    client = get_object_or_404(Client, id=client_id, tenant=request.user.tenant)
    
    # Get all communications for this client
    communications = client.communications.all().order_by('-created_at')
    
    # Calculate communication stats
    email_count = communications.filter(communication_type='EMAIL').count()
    phone_count = communications.filter(communication_type='PHONE').count()
    total_communications = communications.count()
    
    context = {
        'client': client,
        'communications': communications,
        'email_count': email_count,
        'phone_count': phone_count,
        'total_communications': total_communications,
    }
    
    return render(request, 'business_management/client_communications.html', context)