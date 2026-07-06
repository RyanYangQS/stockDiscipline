from pathlib import Path
import os


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_DIR / "data"
DB_PATH = DATA_DIR / "stock_discipline.db"
FRONTEND_DIR = PROJECT_DIR / "frontend"
FRONTEND_DIST_DIR = FRONTEND_DIR / "dist"

APP_NAME = "Stock Discipline"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
