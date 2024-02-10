import os

SCOUT_MONITOR = os.environ.get('SCOUT_MONITOR', 'false').strip() == 'true'

if SCOUT_MONITOR:
    SCOUT_KEY = os.environ.get('SCOUT_KEY', 'invalid').strip()
    SCOUT_NAME = os.environ.get('SCOUT_NAME', 'astrobin').strip()
