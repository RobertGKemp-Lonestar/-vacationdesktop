from django.http import HttpResponse

def minimal_test(request):
    """Absolutely minimal test - no imports from our code"""
    return HttpResponse("""
    <h2>🔧 Minimal Test Endpoint</h2>
    <p>If you can see this, Django is working!</p>
    <p>The 500 errors are likely caused by issues in our custom code.</p>
    <hr>
    <p>Let's check what might be broken:</p>
    <ul>
        <li>Database connection issues</li>
        <li>Missing dependencies</li>
        <li>Import errors in our models</li>
        <li>Template loading issues</li>
    </ul>
    """)