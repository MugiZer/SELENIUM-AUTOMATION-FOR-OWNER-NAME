"""Configuration settings for the application."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).parent.absolute()

# Server configuration
NODE_ENV = os.getenv('NODE_ENV', 'development')
PORT = int(os.getenv('PORT', '3000'))
SESSION_SECRET = os.getenv('SESSION_SECRET')

# Frontend configuration
VITE_API_BASE_URL = os.getenv('VITE_API_BASE_URL', 'http://localhost:3000')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:8080')

# CORS configuration
CORS_ORIGINS = os.getenv('CORS_ORIGIN', 'http://localhost:8080,http://localhost:5173').split(',')

# Scraper credentials
MONTREAL_EMAIL = os.getenv('MONTREAL_EMAIL')
MONTREAL_PASSWORD = os.getenv('MONTREAL_PASSWORD')

# Processing configuration
DELAY_MIN = float(os.getenv('DELAY_MIN', '1.5'))
DELAY_MAX = float(os.getenv('DELAY_MAX', '3.0'))

# File storage configuration
CACHE_PATH = Path(os.getenv('CACHE_PATH', 'cache')).resolve()
INPUT_DIR = Path(os.getenv('INPUT_DIR', 'input')).resolve()
OUTPUT_DIR = Path(os.getenv('OUTPUT_DIR', 'output')).resolve()
LOG_DIR = Path(os.getenv('LOG_DIR', 'logs')).resolve()
BACKUP_DIR = Path(os.getenv('BACKUP_DIR', 'backups')).resolve()

# Ensure directories exist
for directory in [CACHE_PATH, INPUT_DIR, OUTPUT_DIR, LOG_DIR, BACKUP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'info').upper()
LOG_FILE = Path(LOG_DIR) / 'app.log'

# CSV processing
CSV_CHUNK_SIZE = int(os.getenv('CSV_CHUNK_SIZE', '50'))
DATE_FORMAT = os.getenv('DATE_FORMAT', '%Y%m%d_%H%M%S')
INPUT_FILE_PATTERN = os.getenv('INPUT_FILE_PATTERN', '*.csv')
OUTPUT_FILE_PATTERN = os.getenv('OUTPUT_FILE_PATTERN', 'property_data_%Y%m%d_%H%M%S.csv')

# Required input CSV columns
REQUIRED_INPUT_COLUMNS = [
    'civic_number',
    'street_name',
    'postal_code'
]

# Output schema - defines the columns in the output CSV
OUTPUT_COLUMNS = [
    'civic_number',
    'street_name',
    'postal_code',
    'owner_names',
    'owner_type',
    'matricule',
    'tax_account_number',
    'municipality',
    'fiscal_years',
    'nb_logements',
    'assessed_terrain_current',
    'assessed_batiment_current',
    'assessed_total_current',
    'assessed_total_previous',
    'tax_distribution_json',
    'last_fetched_at',
    'source_url',
    'status'
]

# Input CSV expected columns
REQUIRED_INPUT_COLUMNS = ['civic_number', 'street_name', 'postal_code']
OPTIONAL_INPUT_COLUMNS = ['borough', 'notes']

# Borough column name for address matching
BOROUGH_COLUMN = 'borough'
