import os
from pathlib import Path
from dotenv import load_dotenv
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')
def env(k, default=''): return os.getenv(k, default).strip()
DB_PATH = env('DB_PATH', str(BASE_DIR / 'data' / 'crm.sqlite3'))
DEMO_MODE = env('DEMO_MODE', 'true').lower() == 'true'
AI_PROVIDER = env('AI_PROVIDER', 'groq').lower()  # groq or claude
GROQ_API_KEY = env('GROQ_API_KEY')
GROQ_MODEL = env('GROQ_MODEL', 'openai/gpt-oss-120b')
ANTHROPIC_API_KEY = env('ANTHROPIC_API_KEY')
CLAUDE_MODEL = env('CLAUDE_MODEL', 'claude-sonnet-4-5-20250929')
SERPAPI_API_KEY = env('SERPAPI_API_KEY')
GMAIL_CREDENTIALS_FILE = env('GMAIL_CREDENTIALS_FILE', 'credentials.json')
GMAIL_TOKEN_FILE = env('GMAIL_TOKEN_FILE', 'token.json')
GOOGLE_SHEET_ID = env('GOOGLE_SHEET_ID')
GOOGLE_SERVICE_ACCOUNT_FILE = env('GOOGLE_SERVICE_ACCOUNT_FILE', 'service_account.json')
SENDER_NAME = env('SENDER_NAME', 'Campaign Team')
SENDER_EMAIL = env('SENDER_EMAIL')
SENDER_TITLE = env('SENDER_TITLE', 'Partnerships')
POSTAL_ADDRESS = env('POSTAL_ADDRESS')
TEST_RECIPIENT = env('TEST_RECIPIENT')
DAILY_SEND_LIMIT = int(env('DAILY_SEND_LIMIT', '15'))
MIN_SEND_INTERVAL_SECONDS = int(env('MIN_SEND_INTERVAL_SECONDS', '30'))
FOLLOWUP1_DAYS = int(env('FOLLOWUP1_DAYS', '4'))
FOLLOWUP2_DAYS = int(env('FOLLOWUP2_DAYS', '6'))
MIN_SCORE = int(env('MIN_SCORE', '60'))
AUTO_SEND_FOLLOWUPS = env('AUTO_SEND_FOLLOWUPS', 'true').lower() == 'true'
SCHEDULER_POLL_SECONDS = int(env('SCHEDULER_POLL_SECONDS', '900'))
