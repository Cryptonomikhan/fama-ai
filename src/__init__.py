# Make modules directly importable as if they were top-level
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent))

from src import models
