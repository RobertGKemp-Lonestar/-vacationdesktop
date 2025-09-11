from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from rbac.models import Tenant
import uuid

User = get_user_model()


# ============================================================================
# CRM MODELS
# ============================================================================

class Client(models.Model):
    """Travel advisor's client - core contact and preference information"""
    
    LEAD_SOURCE_CHOICES = [
        ('WEBSITE', 'Website Inquiry'),
        ('REFERRAL', 'Referral'),
        ('SOCIAL_MEDIA', 'Social Media'),
        ('EMAIL_MARKETING', 'Email Marketing'),
        ('WALK_IN', 'Walk-in'),
        ('REPEAT_CLIENT', 'Repeat Client'),
        ('OTHER', 'Other'),
    ]
    
    COMMUNICATION_PREFERENCES = [
        ('EMAIL', 'Email'),
        ('PHONE', 'Phone'),
        ('TEXT', 'Text/SMS'),
        ('MAIL', 'Postal Mail'),
    ]
    
    VIP_STATUS_CHOICES = [
        ('REGULAR', 'Regular'),
        ('VIP', 'VIP'),
        ('PREMIUM', 'Premium'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='clients')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='clients_created')
    
    # Basic Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Travel Preferences
    preferred_communication = models.CharField(max_length=20, choices=COMMUNICATION_PREFERENCES, default='EMAIL')
    budget_range_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    budget_range_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preferred_destinations = models.TextField(blank=True, help_text="Comma-separated list of preferred destinations")
    travel_style = models.TextField(blank=True, help_text="Luxury, budget, adventure, family, etc.")
    special_needs = models.TextField(blank=True, help_text="Dietary restrictions, accessibility needs, etc.")
    
    # Business Information
    lead_source = models.CharField(max_length=20, choices=LEAD_SOURCE_CHOICES, default='OTHER')
    is_active = models.BooleanField(default=True)
    vip_status = models.CharField(max_length=20, choices=VIP_STATUS_CHOICES, default='REGULAR')
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_contact_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'clients'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'email']),
            models.Index(fields=['tenant', 'last_name', 'first_name']),
            models.Index(fields=['tenant', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def total_trip_value(self):
        """Calculate total value of all trips for this client"""
        return sum(trip.total_amount or 0 for trip in self.trips.all())


class ClientCommunication(models.Model):
    """Track all communications with clients"""
    
    COMMUNICATION_TYPES = [
        ('EMAIL', 'Email'),
        ('PHONE', 'Phone Call'),
        ('SMS', 'SMS/Text'),
        ('MEETING', 'In-Person Meeting'),
        ('VIDEO_CALL', 'Video Call'),
        ('MAIL', 'Postal Mail'),
        ('OTHER', 'Other'),
    ]
    
    DIRECTION_CHOICES = [
        ('OUTBOUND', 'Outbound'),
        ('INBOUND', 'Inbound'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='communications')
    trip = models.ForeignKey('Trip', on_delete=models.SET_NULL, null=True, blank=True, related_name='communications')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    communication_type = models.CharField(max_length=20, choices=COMMUNICATION_TYPES)
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    subject = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    
    # Email specific fields
    email_message_id = models.CharField(max_length=200, blank=True, help_text="Email Message-ID for threading")
    email_delivery_status = models.CharField(max_length=50, blank=True)
    
    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'client_communications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', 'communication_type']),
            models.Index(fields=['client', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.communication_type} - {self.client.full_name} - {self.created_at.date()}"


class ClientNote(models.Model):
    """Advisor notes about clients"""
    
    NOTE_TYPES = [
        ('GENERAL', 'General Note'),
        ('CALL_LOG', 'Call Log'),
        ('MEETING', 'Meeting Notes'),
        ('PREFERENCE', 'Preference Note'),
        ('ISSUE', 'Issue/Problem'),
        ('FOLLOW_UP', 'Follow-up Required'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='notes')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    note_type = models.CharField(max_length=20, choices=NOTE_TYPES, default='GENERAL')
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    is_important = models.BooleanField(default=False)
    follow_up_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'client_notes'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.note_type} - {self.client.full_name}"


class ClientDocument(models.Model):
    """Store client documents (passports, insurance, etc.)"""
    
    DOCUMENT_TYPES = [
        ('PASSPORT', 'Passport'),
        ('VISA', 'Visa'),
        ('INSURANCE', 'Travel Insurance'),
        ('ID', 'Government ID'),
        ('MEDICAL', 'Medical Records'),
        ('EMERGENCY_CONTACT', 'Emergency Contact'),
        ('PHOTO', 'Photo'),
        ('CONTRACT', 'Contract/Agreement'),
        ('OTHER', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='documents')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='client_documents/%Y/%m/')
    file_size = models.PositiveIntegerField(null=True, blank=True)
    
    # Document metadata
    expiry_date = models.DateField(null=True, blank=True, help_text="For passports, visas, etc.")
    is_verified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'client_documents'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.document_type} - {self.client.full_name}"


# ============================================================================
# TRIP MODELS
# ============================================================================

class Trip(models.Model):
    """Core trip entity linking clients to travel plans"""
    
    STATUS_CHOICES = [
        ('PLANNING', 'Planning'),
        ('SENT_TO_CLIENT', 'Sent to Client'),
        ('WORKING_ON_IT', 'Working On It'),
        ('FINALIZED', 'Finalized'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    TRIP_TYPES = [
        ('CRUISE', 'Cruise'),
        ('TOUR', 'Tour'),
        ('ALL_INCLUSIVE', 'All-Inclusive Resort'),
        ('CONDO_RENTAL', 'Condo/Vacation Rental'),
        ('HOTEL', 'Hotel Stay'),
        ('ADVENTURE', 'Adventure Travel'),
        ('BUSINESS', 'Business Travel'),
        ('HONEYMOON', 'Honeymoon'),
        ('FAMILY', 'Family Vacation'),
        ('GROUP', 'Group Travel'),
        ('OTHER', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='trips')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Trip Details
    trip_name = models.CharField(max_length=200)
    trip_type = models.CharField(max_length=20, choices=TRIP_TYPES, default='CRUISE')
    custom_trip_type = models.CharField(max_length=100, blank=True, help_text="Custom trip type when 'Other' is selected")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNING')
    
    # Dates
    departure_date = models.DateField(null=True, blank=True)
    return_date = models.DateField(null=True, blank=True)
    
    # Locations
    departure_location = models.CharField(max_length=200, blank=True)
    destination = models.CharField(max_length=200, blank=True)
    destinations = models.TextField(blank=True, help_text="Multiple destinations, one per line")
    
    # Pricing
    budget_range_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Minimum budget range")
    budget_range_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Maximum budget range")
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quoted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Actual total amount")
    
    # Trip Details
    number_of_travelers = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True, help_text="Trip description to be included in client emails")
    special_requests = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'trips'
        ordering = ['-departure_date', '-created_at']
        indexes = [
            models.Index(fields=['client', 'status']),
            models.Index(fields=['departure_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.trip_name} - {self.client.full_name}"
    
    @property
    def duration_days(self):
        if self.departure_date and self.return_date:
            return (self.return_date - self.departure_date).days
        return None
    
    @property
    def budget_range_display(self):
        if self.budget_range_min and self.budget_range_max:
            if self.budget_range_min == self.budget_range_max:
                return f"${self.budget_range_min:,.0f}"
            return f"${self.budget_range_min:,.0f} - ${self.budget_range_max:,.0f}"
        elif self.budget_range_min:
            return f"${self.budget_range_min:,.0f}+"
        elif self.budget_range_max:
            return f"Up to ${self.budget_range_max:,.0f}"
        return None
    
    @property
    def is_upcoming(self):
        if self.departure_date:
            return self.departure_date > timezone.now().date()
        return False


class TripLineItem(models.Model):
    """Individual line items for a trip (cruise, airfare, excursions, etc.)"""
    
    ITEM_TYPE_CHOICES = [
        ('CRUISE', 'Cruise'),
        ('AIRFARE', 'Airfare'),
        ('HOTEL', 'Hotel/Accommodation'),
        ('TRANSFER', 'Transfer/Transportation'),
        ('EXCURSION', 'Shore Excursion/Tour'),
        ('INSURANCE', 'Travel Insurance'),
        ('VISA', 'Visa/Documentation'),
        ('RENTAL_CAR', 'Rental Car'),
        ('DINING', 'Dining/Meals'),
        ('ACTIVITIES', 'Activities/Entertainment'),
        ('FEES', 'Fees/Taxes'),
        ('OTHER', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='line_items')
    
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    description = models.CharField(max_length=300)
    supplier = models.CharField(max_length=200, blank=True, help_text="Cruise line, airline, hotel, etc.")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Booking information
    confirmation_number = models.CharField(max_length=100, blank=True)
    booking_date = models.DateField(null=True, blank=True)
    service_date = models.DateField(null=True, blank=True, help_text="Date of service/departure")
    
    # Status
    is_confirmed = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'trip_line_items'
        ordering = ['item_type', 'service_date', 'description']
    
    def save(self, *args, **kwargs):
        # Auto-calculate total_price if not provided
        if not self.total_price:
            self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.get_item_type_display()}: {self.description} (${self.total_price})"


class TripItinerary(models.Model):
    """Day-by-day trip itinerary"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='itinerary_days')
    
    day_number = models.PositiveIntegerField()
    date = models.DateField(null=True, blank=True)
    title = models.CharField(max_length=200, blank=True, help_text="Day title")
    description = models.TextField(blank=True, help_text="Day description and activities")
    location = models.CharField(max_length=200, blank=True)
    
    # Daily details
    accommodation = models.CharField(max_length=200, blank=True)
    activities = models.TextField(blank=True)
    meals = models.TextField(blank=True)
    transportation = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'trip_itineraries'
        ordering = ['trip', 'day_number']
        unique_together = ['trip', 'day_number']
    
    def __str__(self):
        return f"{self.trip.trip_name} - Day {self.day_number}"


class TripParticipant(models.Model):
    """Individual travelers on a trip"""
    
    RELATIONSHIP_CHOICES = [
        ('PRIMARY', 'Primary Traveler'),
        ('SPOUSE', 'Spouse'),
        ('CHILD', 'Child'),
        ('FAMILY', 'Family Member'),
        ('FRIEND', 'Friend'),
        ('COLLEAGUE', 'Colleague'),
        ('OTHER', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='participants')
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    relationship_to_client = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES, default='OTHER')
    passport_number = models.CharField(max_length=50, blank=True)
    passport_expiry = models.DateField(null=True, blank=True)
    
    special_needs = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'trip_participants'
        ordering = ['trip', 'relationship_to_client', 'last_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.trip.trip_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class TripCommunication(models.Model):
    """Trip-specific communications (confirmations, updates, etc.)"""
    
    COMMUNICATION_TYPES = [
        ('QUOTE', 'Quote/Proposal'),
        ('CONFIRMATION', 'Booking Confirmation'),
        ('ITINERARY', 'Itinerary Update'),
        ('PAYMENT_REMINDER', 'Payment Reminder'),
        ('TRAVEL_DOCS', 'Travel Documents'),
        ('PRE_DEPARTURE', 'Pre-Departure Info'),
        ('EMERGENCY', 'Emergency Communication'),
        ('FOLLOW_UP', 'Post-Trip Follow-up'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='trip_communications')
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    communication_type = models.CharField(max_length=20, choices=COMMUNICATION_TYPES)
    subject = models.CharField(max_length=200)
    content = models.TextField()
    
    sent_at = models.DateTimeField(default=timezone.now)
    email_delivered = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'trip_communications'
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"{self.communication_type} - {self.trip.trip_name}"


# ============================================================================
# INVOICE MODELS
# ============================================================================

class Invoice(models.Model):
    """Financial invoices for trips"""
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent'),
        ('VIEWED', 'Viewed by Client'),
        ('PARTIALLY_PAID', 'Partially Paid'),
        ('PAID', 'Paid in Full'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='invoices')
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='invoices')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Invoice Details
    invoice_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    # Amounts
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Dates
    invoice_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    
    # Content
    notes = models.TextField(blank=True)
    terms = models.TextField(blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'invoices'
        ordering = ['-invoice_date']
        indexes = [
            models.Index(fields=['client', 'status']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.client.full_name}"
    
    @property
    def balance_due(self):
        return self.total_amount - self.paid_amount
    
    @property
    def is_overdue(self):
        return self.due_date < timezone.now().date() and self.balance_due > 0


class InvoiceLineItem(models.Model):
    """Individual line items on invoices"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='line_items')
    
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=8, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'invoice_line_items'
        ordering = ['invoice', 'id']
    
    def __str__(self):
        return f"{self.description} - {self.invoice.invoice_number}"


class Payment(models.Model):
    """Track payments made against invoices"""
    
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('CHECK', 'Check'),
        ('CREDIT_CARD', 'Credit Card'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('ONLINE', 'Online Payment'),
        ('OTHER', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_date = models.DateField(default=timezone.now)
    
    # Payment details
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"Payment ${self.amount} - {self.invoice.invoice_number}"


class PaymentSchedule(models.Model):
    """Payment installment schedules"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payment_schedule')
    
    installment_number = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    description = models.CharField(max_length=200, blank=True)
    
    # Linked payment when paid
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'payment_schedules'
        ordering = ['invoice', 'installment_number']
        unique_together = ['invoice', 'installment_number']
    
    def __str__(self):
        return f"Installment {self.installment_number} - {self.invoice.invoice_number}"
    
    @property
    def is_overdue(self):
        return self.due_date < timezone.now().date() and self.status == 'PENDING'