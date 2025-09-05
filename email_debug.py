from django.http import HttpResponse
from django.core.mail import send_mail
from django.conf import settings
import traceback

def email_debug_view(request):
    """Debug email configuration and test sending"""
    debug_info = []
    debug_info.append(f"<h2>📧 Email Configuration Debug</h2>")
    
    try:
        # Show current email settings
        debug_info.append(f"<h3>Current Email Settings:</h3>")
        debug_info.append(f"<p><strong>EMAIL_BACKEND:</strong> {settings.EMAIL_BACKEND}</p>")
        debug_info.append(f"<p><strong>EMAIL_HOST:</strong> {getattr(settings, 'EMAIL_HOST', 'Not set')}</p>")
        debug_info.append(f"<p><strong>EMAIL_HOST_USER:</strong> {getattr(settings, 'EMAIL_HOST_USER', 'Not set')}</p>")
        debug_info.append(f"<p><strong>EMAIL_HOST_PASSWORD:</strong> {'*' * len(getattr(settings, 'EMAIL_HOST_PASSWORD', '')) if getattr(settings, 'EMAIL_HOST_PASSWORD', '') else 'Not set'}</p>")
        debug_info.append(f"<p><strong>EMAIL_PORT:</strong> {getattr(settings, 'EMAIL_PORT', 'Not set')}</p>")
        debug_info.append(f"<p><strong>EMAIL_USE_TLS:</strong> {getattr(settings, 'EMAIL_USE_TLS', 'Not set')}</p>")
        debug_info.append(f"<p><strong>EMAIL_USE_SSL:</strong> {getattr(settings, 'EMAIL_USE_SSL', 'Not set')}</p>")
        debug_info.append(f"<p><strong>DEFAULT_FROM_EMAIL:</strong> {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}</p>")
        
        # Check if we're using SMTP or console
        if settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
            debug_info.append(f"<p>✅ Using SMTP backend - emails should be sent</p>")
        else:
            debug_info.append(f"<p>⚠️ Using {settings.EMAIL_BACKEND} - emails logged to console only</p>")
        
        # Test email sending
        if request.GET.get('test_email'):
            debug_info.append(f"<h3>Testing Email Send:</h3>")
            test_email = request.GET.get('test_email')
            
            try:
                debug_info.append(f"<p>Attempting to send test email to: {test_email}</p>")
                
                result = send_mail(
                    subject='VacationDesktop Email Test',
                    message='This is a test email from VacationDesktop to verify email configuration.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[test_email],
                    html_message=f"""
                    <html>
                    <body>
                        <h2>VacationDesktop Email Test</h2>
                        <p>This is a test email to verify that email configuration is working properly.</p>
                        <p><strong>Sent from:</strong> {settings.DEFAULT_FROM_EMAIL}</p>
                        <p><strong>Backend:</strong> {settings.EMAIL_BACKEND}</p>
                        <p><strong>SMTP Host:</strong> {getattr(settings, 'EMAIL_HOST', 'Not configured')}</p>
                    </body>
                    </html>
                    """,
                    fail_silently=False
                )
                
                debug_info.append(f"<p>✅ Email sent successfully! Return value: {result}</p>")
                debug_info.append(f"<p>Check {test_email} inbox and Mailgun logs</p>")
                
            except Exception as e:
                debug_info.append(f"<p>❌ Email sending failed:</p>")
                debug_info.append(f"<p><strong>Error:</strong> {str(e)}</p>")
                debug_info.append(f"<pre>{traceback.format_exc()}</pre>")
        else:
            debug_info.append(f"<h3>Test Email Sending:</h3>")
            debug_info.append(f"""
            <form method="get">
                <p>Enter email address to test: 
                <input type="email" name="test_email" placeholder="test@example.com" required>
                <input type="submit" value="Send Test Email">
                </p>
            </form>
            """)
        
        return HttpResponse(''.join(debug_info))
        
    except Exception as e:
        return HttpResponse(f"""
        <h2>❌ Email Debug Failed</h2>
        <p>Error: {str(e)}</p>
        <pre>{traceback.format_exc()}</pre>
        """)