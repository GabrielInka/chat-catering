import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
API_DIR = os.path.join(PROJECT_ROOT, "api")

if API_DIR not in sys.path:
    sys.path.insert(0, API_DIR)

from app import app as application  # noqa: E402
from config import validate_runtime_config  # noqa: E402

validate_runtime_config()
