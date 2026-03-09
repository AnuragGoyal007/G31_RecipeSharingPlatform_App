from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
import logging

from .forms import CustomUserCreationForm, CustomUserChangeForm
from recipe_app.models import Recipe
from recipe_app.api_client import FlaskAPIClient

logger = logging.getLogger(__name__)
User = get_user_model()

@never_cache
def register(request):
    """Register via Flask API and sync with Django session"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            # Data for Flask API
            user_data = {
                'username': form.cleaned_data['username'],
                'email': form.cleaned_data['email'],
                'password': form.cleaned_data['password1'], # Standard Django field name in UserCreationForm
                'first_name': form.cleaned_data.get('first_name', ''),
                'last_name': form.cleaned_data.get('last_name', ''),
                'user_type': 'user'
            }
            
            client = FlaskAPIClient()
            try:
                # Create user in Flask API
                api_user = client.create_user(user_data)
                
                # If API success, sync with Django and log in
                user = form.save() # Saves to local DB as well
                
                # Perform login to get token
                auth_result = client.login(user_data['username'], user_data['password'])
                if auth_result and auth_result.get('access_token'):
                    request.session['flask_token'] = auth_result['access_token']
                    
                login(request, user)
                messages.success(request, "Registration successful!")
                return redirect('dashboard')
            except Exception as e:
                logger.error(f"Registration failed in API: {str(e)}")
                messages.error(request, f"Registration failed: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

@never_cache
def user_login(request):
    """Login via Flask API and sync with Django session"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, 'Both username and password are required')
            return render(request, 'users/login.html')
        
        client = FlaskAPIClient()
        try:
            auth_result = client.login(username, password)
            
            if auth_result and auth_result.get('access_token'):
                # Sync user with Django
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': auth_result.get('user', {}).get('email', ''),
                        'is_active': True
                    }
                )
                
                # Store Flask token in session
                request.session['flask_token'] = auth_result['access_token']
                
                # Login in Django context
                login(request, user)
                messages.success(request, 'Logged in successfully!')
                return redirect('dashboard')
            
            messages.error(request, 'Invalid username or password')
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            messages.error(request, 'Authentication service is currently unavailable')
    
    return render(request, 'users/login.html')

@never_cache
@require_GET
@login_required
def dashboard(request):
    user_recipes = Recipe.objects.filter(created_by=request.user)
    
    response = render(request, 'users/dashboard.html', {
        'user': request.user,
        'user_recipes': user_recipes
    })
    
    # Add headers to prevent caching
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response

@login_required
def profile_view(request):
    return render(request, 'users/profile.html', {
        'user': request.user
    })

@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, 'users/profile_edit.html', {'form': form})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was successfully updated!")
            return redirect('profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'users/change_password.html', {'form': form})

def user_logout(request):
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect('home')

@csrf_protect
def csrf_failure(request, reason=""):
    ctx = {'message': 'CSRF verification failed. Please try again.'}
    return render(request, 'csrf_failure.html', ctx)
