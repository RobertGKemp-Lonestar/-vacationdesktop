from django.http import HttpResponse
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
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
        
        # Test email sending with timeout protection
        if request.GET.get('test_email'):
            debug_info.append(f"<h3>Testing Email Send:</h3>")
            test_email = request.GET.get('test_email')
            
            # Force SMTP for this test even if console is default
            force_smtp = request.GET.get('force_smtp') == '1'
            
            if force_smtp:
                debug_info.append(f"<p><strong>FORCING SMTP TEST</strong> (ignoring FORCE_CONSOLE_EMAIL)</p>")
            
            try:
                debug_info.append(f"<p>Attempting to send test email to: {test_email}</p>")
                
                # Import here to avoid timeout issues at startup
                import socket
                socket.setdefaulttimeout(15)  # 15 second socket timeout
                
                # Test connection to SMTP server first
                if force_smtp or settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
                    debug_info.append(f"<p>Testing SMTP connection to {getattr(settings, 'EMAIL_HOST', 'unknown')}:{getattr(settings, 'EMAIL_PORT', 'unknown')}...</p>")
                    
                    try:
                        import smtplib
                        smtp_server = getattr(settings, 'EMAIL_HOST', '')
                        smtp_port = getattr(settings, 'EMAIL_PORT', 587)
                        
                        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
                            if getattr(settings, 'EMAIL_USE_TLS', False):
                                server.starttls()
                            server.login(getattr(settings, 'EMAIL_HOST_USER', ''), getattr(settings, 'EMAIL_HOST_PASSWORD', ''))
                            debug_info.append(f"<p>✅ SMTP connection and authentication successful!</p>")
                            
                    except Exception as smtp_e:
                        debug_info.append(f"<p>❌ SMTP connection failed: {str(smtp_e)}</p>")
                        debug_info.append(f"<p>This explains why emails aren't being sent.</p>")
                
                # Override email backend temporarily for this test
                original_backend = settings.EMAIL_BACKEND
                if force_smtp:
                    settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
                
                result = send_mail(
                    subject='VacationDesktop Email Test - ' + str(timezone.now()),
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
                        <p><strong>Test time:</strong> {timezone.now()}</p>
                    </body>
                    </html>
                    """,
                    fail_silently=False
                )
                
                # Restore original backend
                if force_smtp:
                    settings.EMAIL_BACKEND = original_backend
                
                debug_info.append(f"<p>✅ Email sent successfully! Return value: {result}</p>")
                debug_info.append(f"<p>Check {test_email} inbox and Mailgun logs</p>")
                
            except Exception as e:
                debug_info.append(f"<p>❌ Email sending failed:</p>")
                debug_info.append(f"<p><strong>Error:</strong> {str(e)}</p>")
                debug_info.append(f"<pre>{traceback.format_exc()}</pre>")
                
                # Restore original backend if it was changed
                if force_smtp and 'original_backend' in locals():
                    settings.EMAIL_BACKEND = original_backend
        else:
            debug_info.append(f"<h3>Test Email Sending:</h3>")
            debug_info.append(f"""
            <form method="get">
                <p>Enter email address to test: 
                <input type="email" name="test_email" placeholder="test@example.com" required>
                <br><br>
                <label>
                <input type="checkbox" name="force_smtp" value="1"> 
                Force SMTP test (ignore FORCE_CONSOLE_EMAIL setting)
                </label>
                <br><br>
                <input type="submit" value="Send Test Email">
                </p>
            </form>
            <p><strong>Note:</strong> Check "Force SMTP test" to test actual Mailgun connection even when console backend is active.</p>
            """)
        
        return HttpResponse(''.join(debug_info))
        
    except Exception as e:
        return HttpResponse(f"""
        <h2>❌ Email Debug Failed</h2>
        <p>Error: {str(e)}</p>
        <pre>{traceback.format_exc()}</pre>
        """)