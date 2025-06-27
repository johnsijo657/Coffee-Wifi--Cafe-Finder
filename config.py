import os
from dotenv import load_dotenv  # Optional but recommended

# Load environment variables from .env file
load_dotenv()

class Config:
    # Secret key for session security
    SECRET_KEY = os.environ.get('SECRET_KEY') 
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') 
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False