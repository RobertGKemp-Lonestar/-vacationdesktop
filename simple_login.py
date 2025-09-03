from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def emergency_login(request):
    """Emergency login bypass"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/simple-dashboard/')
        else:
            return HttpResponse("❌ Invalid credentials")
    
    return HttpResponse("""
    <html>
    <head><title>Emergency Login</title></head>
    <body>
        <h2>Emergency Login</h2>
        <form method="post">
            <p>Username: <input type="text" name="username" value="admin"></p>
            <p>Password: <input type="password" name="password" value="VacationAdmin2024!"></p>
            <p><input type="submit" value="Login"></p>
        </form>
    </body>
    </html>
    """)