from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.contrib.auth import login as django_login, logout as django_logout, authenticate, get_user_model
import logging

from .models import Recipe, Comment, ContactMessage
from .forms import RecipeForm, CommentForm, ContactForm
from .api_client import FlaskAPIClient, FlaskAPIError

logger = logging.getLogger(__name__)
User = get_user_model()

# --- Flask API Backend Views ---

def recipe_list(request):
    """List all recipes from Flask API"""
    client = FlaskAPIClient()
    category = request.GET.get('category')
    
    try:
        recipes = client.get_recipes(category=category)
        if not recipes:
            messages.warning(request, 'No recipes found')
            recipes = []
        return render(request, 'recipes/list.html', {'recipes': recipes, 'category': category})
    except FlaskAPIError as e:
        messages.error(request, f'API Error: {str(e)}')
        return render(request, 'recipes/list.html', {'recipes': []})

def recipe_detail(request, pk):
    """View details of a recipe from Flask API"""
    client = FlaskAPIClient()
    try:
        recipe = client.get_recipe(pk)  
        return render(request, 'recipes/flask_recipe_detail.html', {'recipe': recipe})
    except Exception as e:
        logger.error(f"Error fetching recipe {pk}: {str(e)}")
        return render(request, 'error.html', {'message': "Recipe not found or API error"})

def user_login(request):
    """Login via Flask API and sync with Django session"""
    if request.user.is_authenticated:
        return redirect('home')

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
                # Sync user with Django - Password is not stored in Django for security (unusable)
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': auth_result.get('user', {}).get('email', ''),
                        'is_active': True
                    }
                )
                
                request.session['flask_token'] = auth_result['access_token']
                django_login(request, user)
                messages.success(request, 'Logged in successfully!')
                return redirect('home')
            
            messages.error(request, 'Invalid credentials')
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            messages.error(request, 'Connection to authentication service failed')
    
    return render(request, 'users/login.html')

@login_required
def user_logout(request):
    """Logout and clear Flask token"""
    if 'flask_token' in request.session:
        del request.session['flask_token']
    django_logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')

@login_required
def recipe_create(request):
    """Create a recipe via Flask API"""
    if not request.session.get('flask_token'):
        messages.error(request, "Please login to create recipes")
        return redirect('user_login')

    if request.method == 'POST':
        try:
            form_data = {
                'title': request.POST.get('title', '').strip(),
                'description': request.POST.get('description', '').strip(),
                'ingredients': request.POST.get('ingredients', '').strip(),
                'cooking_method': request.POST.get('cooking_method', '').strip(),
                'calorie_count': int(request.POST.get('calorie_count', 0)),
                'cooking_time': int(request.POST.get('cooking_time', 0)),
                'category': request.POST.get('category', 'veg'),
                'allergic_content': request.POST.get('allergic_content', '').strip(),
            }

            if not all([form_data['title'], form_data['description'], form_data['ingredients'], form_data['cooking_method']]):
                raise ValueError("All required fields must be filled")

            client = FlaskAPIClient(request)
            response = client.create_recipe(form_data)
            messages.success(request, "Recipe created successfully!")
            return redirect('recipe_detail', pk=response.get('id'))
            
        except ValueError as e:
            messages.error(request, f"Validation error: {str(e)}")
        except FlaskAPIError as e:
            messages.error(request, f"API Error: {str(e)}")
        except Exception as e:
            logger.exception("Unexpected error in recipe_create")
            messages.error(request, "Unexpected error occurred")

        return render(request, 'recipes/recipe_create.html', {
            'form_data': request.POST.dict()
        })
    
    return render(request, 'recipes/recipe_create.html')

# --- Legacy/Shared Views (Synchronized with Flask where possible) ---

def home(request):
    """Home page - defaults to recipe_list (API)"""
    return recipe_list(request)

@login_required
def my_recipes(request):
    """Show recipes created by current user (via API or local sync)"""
    client = FlaskAPIClient(request)
    try:
        # Since we don't have a direct 'my-recipes' endpoint, filter all recipes
        # In a real app, add a user-specific endpoint to the Flask API
        all_recipes = client.get_recipes()
        user_recipes = [r for r in all_recipes if r.get('created_by_id') == request.user.id]
        return render(request, 'recipes/my_recipes.html', {'recipes': user_recipes})
    except Exception as e:
        logger.error(f"Error fetching user recipes: {str(e)}")
        # Fallback to local Django DB if API fails
        recipes = Recipe.objects.filter(created_by=request.user)
        return render(request, 'recipes/my_recipes.html', {'recipes': recipes})

@login_required
def recipe_delete(request, pk):
    """Delete a recipe via Flask API"""
    client = FlaskAPIClient(request)
    if request.method == 'POST':
        try:
            client.delete_recipe(pk)
            messages.success(request, "Recipe deleted successfully")
            return redirect('my_recipes')
        except Exception as e:
            messages.error(request, f"Failed to delete: {str(e)}")
    
    # Try to get recipe info for confirmation page
    try:
        recipe = client.get_recipe(pk)
    except:
        recipe = None
    return render(request, 'recipes/recipe_delete.html', {'recipe': recipe})

@login_required
def recipe_update(request, pk):
    """Update a recipe via Flask API"""
    client = FlaskAPIClient(request)
    try:
        recipe = client.get_recipe(pk)
        if recipe.get('created_by_id') != request.user.id and not request.user.is_staff:
            return HttpResponseForbidden("You are not allowed to edit this recipe.")
        
        if request.method == 'POST':
            form_data = {
                'title': request.POST.get('title', '').strip(),
                'description': request.POST.get('description', '').strip(),
                'ingredients': request.POST.get('ingredients', '').strip(),
                'cooking_method': request.POST.get('cooking_method', '').strip(),
                'calorie_count': int(request.POST.get('calorie_count', 0)),
                'cooking_time': int(request.POST.get('cooking_time', 0)),
                'category': request.POST.get('category', 'veg'),
                'allergic_content': request.POST.get('allergic_content', '').strip(),
            }
            client.update_recipe(pk, form_data)
            messages.success(request, "Recipe updated successfully!")
            return redirect('recipe_detail', pk=pk)
        
        return render(request, 'recipes/recipe_update.html', {'recipe': recipe})
    except Exception as e:
        logger.error(f"Error updating recipe {pk}: {str(e)}")
        messages.error(request, f"Update failed: {str(e)}")
        return redirect('recipe_detail', pk=pk)

@login_required
def add_comment(request, pk):
    """Add a comment via Flask API"""
    if request.method == 'POST':
        content = request.POST.get('content')
        if not content:
            messages.error(request, "Comment cannot be empty")
            return redirect('recipe_detail', pk=pk)
        
        client = FlaskAPIClient(request)
        try:
            client.create_comment(pk, content, request.user.id)
            messages.success(request, "Comment added!")
        except Exception as e:
            messages.error(request, f"Failed to add comment: {str(e)}")
    return redirect('recipe_detail', pk=pk)

@login_required
def delete_comment(request, pk):
    """Delete a comment via Flask API"""
    client = FlaskAPIClient(request)
    try:
        # In a real app, you'd get the comment details first to find the recipe_id
        # for redirection, but for now we follow the API path.
        client.delete_comment(pk)
        messages.success(request, "Comment deleted")
    except Exception as e:
        messages.error(request, f"Failed to delete comment: {str(e)}")
    return redirect('home') # Redirect home since we don't naturally know the recipe_id here

def contact_us(request):
    """Contact form submission"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            client = FlaskAPIClient()
            try:
                client.create_contact_message(
                    name=form.cleaned_data['name'],
                    email=form.cleaned_data['email'],
                    message=form.cleaned_data['message']
                )
                messages.success(request, 'Your message has been sent to our team!')
                return redirect('home')
            except Exception as e:
                logger.error(f"Failed to send contact message via API: {str(e)}")
                ContactMessage.objects.create(**form.cleaned_data)
                messages.success(request, 'Your message has been saved locally.')
                return redirect('home')
    else:
        form = ContactForm()
    return render(request, 'recipes/contact_us.html', {'form': form})
