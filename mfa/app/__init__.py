from flask import Flask
from flask_mail import Mail
# from flask_mysqldb import MySQL # Remove MySQL
from .config import Config
from supabase import create_client, Client # Add Supabase imports
import os

mail = Mail()
# mysql = MySQL() # Remove MySQL instance

# Create Supabase client instance
supabase: Client = None

def create_app():
    global supabase # Allow modification of the global variable

    app = Flask(__name__)
    app.config.from_object(Config)

    # Check if Supabase credentials are provided
    if not app.config.get('SUPABASE_URL') or not app.config.get('SUPABASE_ANON_KEY'):
        raise ValueError("Supabase URL and Anon Key must be set in config or .env file.")

    # Initialize Supabase client
    supabase = create_client(
        app.config['SUPABASE_URL'],
        app.config['SUPABASE_ANON_KEY']
    )

    mail.init_app(app)
    # mysql.init_app(app) # Remove MySQL init

    from .routes import mfa
    app.register_blueprint(mfa)

    return app

# Function to get the initialized Supabase client easily in other modules
def get_supabase_client():
    if supabase is None:
        raise Exception("Supabase client not initialized. Call create_app first.")
    return supabase