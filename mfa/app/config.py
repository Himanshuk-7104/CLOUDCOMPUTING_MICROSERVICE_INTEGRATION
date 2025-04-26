import os
from dotenv import load_dotenv

load_dotenv() # Load variables from .env file

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_secret_key_here') # Keep or use env var

    # Remove MySQL Config
    # MYSQL_HOST = 'localhost'
    # MYSQL_USER = 'root'
    # MYSQL_PASSWORD = 'my_password_here'
    # MYSQL_DB = 'virtual_labs'

    # Add Supabase Config (loaded from .env)
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY')

    # Keep Flask-Mail Config
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') # Get from .env or hardcode if needed
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') # Get from .env (Gmail App Password)