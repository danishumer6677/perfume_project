import os
import sys
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_dir))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'perfume_project.settings')

# Import Django WSGI application
from perfume_project.wsgi import application

# Vercel expects the WSGI app to be named 'app'
app = application
