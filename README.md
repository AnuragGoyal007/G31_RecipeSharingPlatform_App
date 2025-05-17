# 🍳 Recipe Sharing Platform

A full-stack web application that allows users to share, discover, and manage recipes. Built with Django and Flask, this platform provides a seamless experience for food enthusiasts to connect through their culinary creations.

## 🌟 Features

- 👤 User Authentication & Authorization
- 📝 Recipe Management (Create, Read, Update, Delete)
- 🏷️ Recipe Categorization (Vegetarian/Non-Vegetarian)
- 💬 Comment System
- 📸 Image Upload Support
- 🔍 Recipe Search & Filtering
- 📱 Responsive Design
- 📧 Contact Form
- 🔐 Secure API Integration

## 🛠️ Tech Stack

- **Backend**: Django, Flask
- **Frontend**: HTML, CSS, Bootstrap
- **Database**: SQLite
- **Authentication**: Django Auth + Custom Flask Auth
- **File Storage**: Local Media Storage

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip (Python package manager)
- virtualenv (recommended)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/RecipeSharingPlatform_App.git
cd RecipeSharingPlatform_App
```

2. Create and activate virtual environment:
```bash
# Windows
python -m venv env
.\env\Scripts\activate

# Linux/Mac
python3 -m venv env
source env/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the database:
```bash
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

7. Start the Flask API server (in a separate terminal):
```bash
cd flask_app
python app.py
```

## 📡 API Endpoints

### Authentication
- `POST /api/login` - User login
- `POST /api/logout` - User logout

### Recipes
- `GET /api/recipes` - List all recipes
- `GET /api/recipes/{id}` - Get recipe details
- `POST /api/recipes` - Create new recipe
- `PUT /api/recipes/{id}` - Update recipe
- `DELETE /api/recipes/{id}` - Delete recipe

### Comments
- `GET /api/recipes/{id}/comments` - Get recipe comments
- `POST /api/recipes/{id}/comments` - Add comment

### Contact
- `POST /api/contact` - Send contact message
- `GET /api/contact` - Get all messages (admin only)

## 🔑 Environment Variables

Create a `.env` file in the root directory:

```env
DEBUG=True
SECRET_KEY=your_secret_key
FLASK_API_URL=http://localhost:5000
MEDIA_URL=/media/
MEDIA_ROOT=media/
```

## 📱 Usage Examples

### Creating a Recipe
```python
import requests

def create_recipe(token, recipe_data):
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.post(
        'http://localhost:5000/api/recipes',
        json=recipe_data,
        headers=headers
    )
    return response.json()

# Example usage
recipe_data = {
    'title': 'Pasta Carbonara',
    'description': 'Classic Italian pasta dish',
    'ingredients': 'Spaghetti, Eggs, Bacon, Parmesan',
    'cooking_method': '1. Boil pasta\n2. Fry bacon\n3. Mix eggs and cheese',
    'calorie_count': 650,
    'cooking_time': 30,
    'category': 'nonveg'
}
```

### Fetching Recipes
```python
def get_recipes(category=None):
    params = {'category': category} if category else {}
    response = requests.get('http://localhost:5000/api/recipes', params=params)
    return response.json()
```

## 🔮 Future Scope

1. **Enhanced Features**
   - Recipe rating system
   - User profiles with favorite recipes
   - Recipe sharing via social media
   - Recipe scaling calculator
   - Nutritional information calculator

2. **Technical Improvements**
   - Docker containerization
   - CI/CD pipeline integration
   - Unit and integration tests
   - API rate limiting
   - Caching implementation

3. **User Experience**
   - Dark mode support
   - Recipe print view
   - Shopping list generator
   - Meal planning calendar
   - Recipe recommendations based on user preferences

4. **Social Features**
   - User following system
   - Recipe collections
   - Cooking challenges
   - Community events
   - Recipe contests

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 👥 Authors

- Your Name - Initial work

## 🙏 Acknowledgments

- Django Documentation
- Flask Documentation
- Bootstrap Documentation
