import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')

# --- Secrets (loaded from .env) ---
SECRET_KEY = os.environ['SECRET_KEY']
EMAIL_PASSWORD = os.environ['EMAIL_PASSWORD']
EMAIL_SENDER = os.environ['EMAIL_SENDER']
EMAIL_USERNAME = os.environ['EMAIL_USERNAME']
EMAIL_RECEIVERS = os.environ['EMAIL_RECEIVERS'].split(',')
EXCEL_OUTPUT_DIR = os.environ['EXCEL_OUTPUT_DIR']

# --- Non-secret config ---
DATABASE = 'machine_evidency.db'
PERMANENT_SESSION_LIFETIME = timedelta(hours=3)

EMAIL_SMTP_SERVER = 'smtp-mail.outlook.com'
EMAIL_PORT = 587

COLUMN_RENAME_MAP = {
    'registration_number': 'Registračné/evidenčné číslo',
    'name': 'Názov',
    'revision_date': 'Dátum revízie',
    'revision_periodicity': 'Interval revízie',
    'protocol': 'Číslo protokolu',
    'type': 'Typ',
    'manufacturing_number': 'Výrobné číslo',
    'manufacturer': 'Výrobca',
    'location': 'Lokácia',
    'owner': 'Vlastník',
    'registration_date': 'Dátum registrácie',
    'note': 'Poznámka',
    'validation': 'Platnosť revízie',
}