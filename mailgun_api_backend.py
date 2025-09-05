"""
Mailgun HTTP API email backend for Django
More reliable than SMTP on cloud platforms like Railway
"""
import requests
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import sanitize_address
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class MailgunAPIBackend(BaseEmailBackend):
    """
    Email backend that uses Mailgun's HTTP API instead of SMTP
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_key = getattr(settings, 'MAILGUN_API_KEY', '')
        self.domain = getattr(settings, 'MAILGUN_DOMAIN', '')
        
        # Extract domain from EMAIL_HOST_USER if not explicitly set
        if not self.domain and hasattr(settings, 'EMAIL_HOST_USER'):
            # forms@kemp-it.com -> kemp-it.com
            if '@' in settings.EMAIL_HOST_USER:
                self.domain = settings.EMAIL_HOST_USER.split('@')[1]
    
    def send_messages(self, email_messages):
        """
        Send email messages using Mailgun API
        """
        if not self.api_key:
            logger.error("MAILGUN_API_KEY not configured")
            return 0
            
        if not self.domain:
            logger.error("MAILGUN_DOMAIN not configured")
            return 0
        
        sent_count = 0
        
        for message in email_messages:
            if self._send_message(message):
                sent_count += 1
        
        return sent_count
    
    def _send_message(self, message):
        """
        Send a single email message via Mailgun API
        """
        try:
            # Prepare API request
            url = f"https://api.mailgun.net/v3/{self.domain}/messages"
            
            # Handle multiple recipients
            to_emails = [sanitize_address(addr, message.encoding) for addr in message.to]
            
            data = {
                'from': sanitize_address(message.from_email, message.encoding),
                'to': to_emails,
                'subject': message.subject,
                'text': message.body,
            }
            
            # Add HTML version if available
            for alternative in message.alternatives:
                content, content_type = alternative
                if content_type == 'text/html':
                    data['html'] = content
                    break
            
            # Add CC and BCC if present
            if message.cc:
                data['cc'] = [sanitize_address(addr, message.encoding) for addr in message.cc]
            if message.bcc:
                data['bcc'] = [sanitize_address(addr, message.encoding) for addr in message.bcc]
            
            # Make API request
            response = requests.post(
                url,
                auth=('api', self.api_key),
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"Email sent successfully via Mailgun API: {message.subject}")
                return True
            else:
                logger.error(f"Mailgun API error {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send email via Mailgun API: {str(e)}")
            return False