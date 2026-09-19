import os

ADMIN_TOKEN = os.getenv('ADV_LAB_ADMIN_TOKEN', 'adv-lab-admin')
DATABASE_URL = os.getenv('ADV_LAB_DATABASE_URL', 'sqlite:///./database.db')
INSTAGRAM_USERNAME = os.getenv('ADV_LAB_INSTAGRAM', 'astrodevic')
NASA_API_KEY = os.getenv('ADV_LAB_NASA_API_KEY', 'DEMO_KEY')
ALLOWED_HOSTS = [host.strip() for host in os.getenv('ADV_LAB_ALLOWED_HOSTS', 'localhost,127.0.0.1,[::1],testserver').split(',') if host.strip()]
