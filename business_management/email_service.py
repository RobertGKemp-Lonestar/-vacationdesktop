"""
Email service layer for multi-tenant communications
Supports single-domain development and multi-domain production scaling
"""
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from rbac.models import Tenant
from .models import ClientCommunication
import logging

logger = logging.getLogger(__name__)


class TenantEmailService:
    """
    Scalable email service that supports both single-domain development
    and multi-domain production environments
    """
    
    def __init__(self, tenant=None):
        self.tenant = tenant
    
    def get_sending_domain(self):
        """
        Get the appropriate sending domain for this tenant
        Development: Single domain for all tenants
        Production: Individual domain per tenant
        """
        if settings.DEBUG or not hasattr(settings, 'MAILGUN_MULTI_DOMAIN_ENABLED'):
            # Development mode - use single domain
            return getattr(settings, 'MAILGUN_DEVELOPMENT_DOMAIN', 'mail.vacationdesktop.com')
        else:
            # Production mode - tenant-specific domains
            if self.tenant and self.tenant.subdomain:
                base_domain = getattr(settings, 'MAILGUN_BASE_DOMAIN', 'vacationdesktop.com')
                return f'{self.tenant.subdomain}.{base_domain}'
            else:
                # Fallback to main domain
                return getattr(settings, 'MAILGUN_DEFAULT_DOMAIN', 'mail.vacationdesktop.com')
    
    def get_sender_email(self, advisor_name=None):
        """
        Generate the appropriate sender email address
        Format: advisor@domain.com or system@domain.com
        """
        domain = self.get_sending_domain()
        
        if advisor_name:
            # Clean advisor name for email (remove spaces, special chars)
            clean_name = ''.join(c.lower() for c in advisor_name if c.isalnum())
            return f'{clean_name}@{domain}'
        else:
            return f'system@{domain}'
    
    def send_client_email(self, client, subject, template_name, context=None, 
                         sender_name=None, communication_type='EMAIL', trip=None):
        """
        Send an email to a client with proper tracking and threading
        
        Args:
            client: Client model instance
            subject: Email subject line
            template_name: Django template name (without .html)
            context: Template context dictionary
            sender_name: Name for sender email address
            communication_type: Type from ClientCommunication.COMMUNICATION_TYPES
            trip: Optional Trip model instance
            
        Returns:
            tuple: (success: bool, communication_record: ClientCommunication)
        """
        if not client.email:
            logger.warning(f"No email address for client {client.full_name}")
            return False, None
        
        # Prepare context with absolute URLs for logos and tenant info
        tenant_logo_url = None
        if self.tenant and self.tenant.logo:
            # Create absolute URL for logo in emails
            from django.contrib.sites.shortcuts import get_current_site
            from django.urls import reverse
            try:
                # Try to get current site for absolute URL
                domain = getattr(settings, 'SITE_DOMAIN', 'localhost:8000')
                protocol = 'https' if not settings.DEBUG else 'http'
                tenant_logo_url = f"{protocol}://{domain}{self.tenant.logo.url}"
            except:
                # Fallback to relative URL
                tenant_logo_url = self.tenant.logo.url
        
        email_context = {
            'client': client,
            'tenant': self.tenant,
            'tenant_name': self.tenant.name if self.tenant else None,
            'tenant_logo': tenant_logo_url,
            'subject': subject,
            # Add tenant contact info for footer
            'sender_email': self.tenant.contact_email if self.tenant else None,
            'sender_phone': self.tenant.phone if self.tenant else None,
            'sender_name': sender_name or (self.tenant.name if self.tenant else None),
            **(context or {})
        }
        
        # Render email templates
        html_message = render_to_string(f'emails/{template_name}.html', email_context)
        plain_message = strip_tags(html_message)
        
        # Generate sender email
        sender_email = self.get_sender_email(sender_name)
        
        # Create communication record
        communication = ClientCommunication.objects.create(
            client=client,
            trip=trip,
            created_by=None,  # Will be set by view if available
            communication_type=communication_type,
            direction='OUTBOUND',
            subject=subject,
            content=plain_message,
            scheduled_at=timezone.now()
        )
        
        try:
            # Send email
            success = send_mail(
                subject=subject,
                message=plain_message,
                from_email=sender_email,
                recipient_list=[client.email],
                html_message=html_message,
                fail_silently=False
            )
            
            # Update communication record
            communication.sent_at = timezone.now()
            communication.email_delivery_status = 'SENT' if success else 'FAILED'
            communication.save()
            
            logger.info(f"Email sent to {client.email}: {subject}")
            return True, communication
            
        except Exception as e:
            # Update communication record with error
            communication.email_delivery_status = f'ERROR: {str(e)}'
            communication.save()
            
            logger.error(f"Failed to send email to {client.email}: {str(e)}")
            return False, communication
    
    def send_trip_confirmation(self, trip, sender_name=None):
        """Send trip confirmation email to client"""
        return self.send_client_email(
            client=trip.client,
            subject=f'Trip Confirmation - {trip.trip_name}',
            template_name='trip_confirmation',
            context={'trip': trip},
            sender_name=sender_name,
            communication_type='EMAIL',
            trip=trip
        )
    
    def send_payment_reminder(self, invoice, sender_name=None):
        """Send payment reminder email"""
        return self.send_client_email(
            client=invoice.client,
            subject=f'Payment Reminder - Invoice {invoice.invoice_number}',
            template_name='payment_reminder',
            context={'invoice': invoice, 'trip': invoice.trip},
            sender_name=sender_name,
            communication_type='EMAIL',
            trip=invoice.trip
        )
    
    def send_itinerary_update(self, trip, sender_name=None):
        """Send itinerary update email"""
        return self.send_client_email(
            client=trip.client,
            subject=f'Itinerary Update - {trip.trip_name}',
            template_name='itinerary_update',
            context={'trip': trip, 'itinerary_days': trip.itinerary_days.all()},
            sender_name=sender_name,
            communication_type='EMAIL',
            trip=trip
        )
    
    def send_pre_departure_checklist(self, trip, sender_name=None):
        """Send pre-departure checklist email"""
        return self.send_client_email(
            client=trip.client,
            subject=f'Pre-Departure Checklist - {trip.trip_name}',
            template_name='pre_departure_checklist',
            context={'trip': trip, 'participants': trip.participants.all()},
            sender_name=sender_name,
            communication_type='EMAIL',
            trip=trip
        )


class CommunicationManager:
    """
    High-level communication management for automated workflows
    """
    
    @staticmethod
    def get_email_service(tenant):
        """Get email service instance for tenant"""
        return TenantEmailService(tenant)
    
    @staticmethod
    def schedule_trip_communications(trip):
        """
        Schedule automated communications for a trip based on status
        """
        email_service = CommunicationManager.get_email_service(trip.client.tenant)
        
        if trip.status == 'BOOKED':
            # Send confirmation email
            return email_service.send_trip_confirmation(trip)
        
        elif trip.status == 'CONFIRMED':
            # Check if departure is within 30 days
            if trip.departure_date and trip.is_upcoming:
                days_until_departure = (trip.departure_date - timezone.now().date()).days
                if days_until_departure <= 30:
                    return email_service.send_pre_departure_checklist(trip)
        
        return False, None
    
    @staticmethod
    def schedule_payment_reminders(invoice):
        """
        Schedule payment reminder based on invoice status and due date
        """
        email_service = CommunicationManager.get_email_service(invoice.client.tenant)
        
        if invoice.status in ['SENT', 'VIEWED'] and invoice.balance_due > 0:
            # Check if payment is due soon or overdue
            days_until_due = (invoice.due_date - timezone.now().date()).days
            
            if days_until_due <= 3 or invoice.is_overdue:
                return email_service.send_payment_reminder(invoice)
        
        return False, None


# Utility functions for webhooks and reply processing
class EmailWebhookProcessor:
    """
    Process incoming email webhooks from Mailgun for reply handling
    """
    
    @staticmethod
    def process_mailgun_webhook(webhook_data):
        """
        Process incoming Mailgun webhook for email replies
        This will be implemented when Mailgun webhooks are set up
        """
        # Extract email data from webhook
        sender = webhook_data.get('sender')
        recipient = webhook_data.get('recipient')
        subject = webhook_data.get('subject', '')
        body = webhook_data.get('body-plain', '')
        message_id = webhook_data.get('Message-Id', '')
        
        # Find the client based on sender email
        from .models import Client
        try:
            client = Client.objects.get(email=sender)
            
            # Create inbound communication record
            communication = ClientCommunication.objects.create(
                client=client,
                communication_type='EMAIL',
                direction='INBOUND',
                subject=subject,
                content=body,
                email_message_id=message_id,
                email_delivery_status='RECEIVED'
            )
            
            # TODO: Notify advisor of new reply
            # TODO: Parse and link to existing conversation thread
            
            logger.info(f"Processed inbound email from {sender}")
            return True, communication
            
        except Client.DoesNotExist:
            logger.warning(f"Received email from unknown sender: {sender}")
            return False, None
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return False, None


# Settings validation
def validate_email_configuration():
    """
    Validate email configuration on startup
    """
    required_settings = [
        'EMAIL_HOST_USER',
        'EMAIL_HOST_PASSWORD',
        'DEFAULT_FROM_EMAIL'
    ]
    
    missing_settings = []
    for setting in required_settings:
        if not hasattr(settings, setting) or not getattr(settings, setting):
            missing_settings.append(setting)
    
    if missing_settings:
        logger.warning(f"Missing email settings: {', '.join(missing_settings)}")
        return False
    
    logger.info("Email configuration validated successfully")
    return True