from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, get_user_model
from django.views.decorators.csrf import csrf_exempt
import traceback
import sys

@csrf_exempt
def emergency_login_debug(request):
    """Emergency login with detailed debugging"""
    debug_info = []
    
    try:
        debug_info.append(f"<h2>🔧 Emergency Login Debug</h2>")
        debug_info.append(f"<p><strong>Request method:</strong> {request.method}</p>")
        
        if request.method == 'POST':
            debug_info.append(f"<p><strong>Processing POST request...</strong></p>")
            
            username = request.POST.get('username')
            password = request.POST.get('password')
            
            debug_info.append(f"<p><strong>Username received:</strong> {username}</p>")
            debug_info.append(f"<p><strong>Password received:</strong> {'*' * len(password) if password else 'None'}</p>")
            
            # Test User model access
            try:
                User = get_user_model()
                debug_info.append(f"<p>✅ get_user_model() works: {User}</p>")
                
                # Check if user exists
                try:
                    user_exists = User.objects.filter(username=username).exists()
                    debug_info.append(f"<p><strong>User exists:</strong> {user_exists}</p>")
                    
                    if user_exists:
                        user_obj = User.objects.get(username=username)
                        debug_info.append(f"<p><strong>User found:</strong> {user_obj.username} (ID: {user_obj.id})</p>")
                        debug_info.append(f"<p><strong>User is_active:</strong> {user_obj.is_active}</p>")
                        debug_info.append(f"<p><strong>User role:</strong> {getattr(user_obj, 'role', 'No role')}</p>")
                        debug_info.append(f"<p><strong>User tenant:</strong> {getattr(user_obj, 'tenant', 'No tenant')}</p>")
                    
                except Exception as e:
                    debug_info.append(f"<p>❌ User lookup failed: {str(e)}</p>")
                    debug_info.append(f"<pre>{traceback.format_exc()}</pre>")
                    
            except Exception as e:
                debug_info.append(f"<p>❌ get_user_model() failed: {str(e)}</p>")
                debug_info.append(f"<pre>{traceback.format_exc()}</pre>")
            
            # Test authentication
            try:
                debug_info.append(f"<p><strong>Attempting authentication...</strong></p>")
                user = authenticate(request, username=username, password=password)
                
                if user is not None:
                    debug_info.append(f"<p>✅ Authentication successful: {user}</p>")
                    
                    # Test login
                    try:
                        debug_info.append(f"<p><strong>Attempting login...</strong></p>")
                        login(request, user)
                        debug_info.append(f"<p>✅ Login successful</p>")
                        debug_info.append(f"<p><strong>Session key:</strong> {request.session.session_key}</p>")
                        debug_info.append(f"<p><strong>User authenticated:</strong> {request.user.is_authenticated}</p>")
                        
                        # Try redirect
                        debug_info.append(f"<p><strong>Attempting redirect to /simple-dashboard/...</strong></p>")
                        debug_info.append(f"<p><a href='/simple-dashboard/'>Click here to go to dashboard</a></p>")
                        
                    except Exception as e:
                        debug_info.append(f"<p>❌ Login failed: {str(e)}</p>")
                        debug_info.append(f"<pre>{traceback.format_exc()}</pre>")
                        
                else:
                    debug_info.append(f"<p>❌ Authentication failed - invalid credentials</p>")
                    
            except Exception as e:
                debug_info.append(f"<p>❌ Authentication process failed: {str(e)}</p>")
                debug_info.append(f"<pre>{traceback.format_exc()}</pre>")
                
        else:
            # Display form
            debug_info.append(f"""
            <form method="post">
                <p>Username: <input type="text" name="username" value="admin"></p>
                <p>Password: <input type="password" name="password" value="VacationAdmin2024!"></p>
                <p><input type="submit" value="Debug Login"></p>
            </form>
            """)
        
        return HttpResponse(''.join(debug_info))
        
    except Exception as e:
        return HttpResponse(f"""
        <h2>❌ Emergency Login Debug Failed</h2>
        <p>Error: {str(e)}</p>
        <pre>{traceback.format_exc()}</pre>
        """)