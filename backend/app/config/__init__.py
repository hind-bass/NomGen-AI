import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / 'categories.json'

def load_categories_config():
    """Load category configuration from JSON file."""
    with open(CONFIG_PATH, encoding='utf-8') as f:
        return json.load(f)

# Load config at module import time
CATEGORIES_CONFIG = load_categories_config()
