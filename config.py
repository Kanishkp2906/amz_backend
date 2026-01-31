import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('db_url')
CRON_SECRET = os.getenv('cron_secret')
EMAIL_ID = os.getenv('email_id')
EMAIL_PASSWORD = os.getenv('email_password')
SMTP_SERVER = os.getenv('smtp_server')
SMTP_PORT = int(os.getenv('smtp_port'))
REDIS_URL = os.getenv('redis_url')