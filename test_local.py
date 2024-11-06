import os
import sys
from dotenv import load_dotenv
from asyncio import run

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
load_dotenv()

# Set DEBUG_RUN to True for local testing
os.environ["DEBUG_RUN"] = "True"
os.environ["INPUT_DEBUG_LOGGING"] = "True"

from sources.main import main

if __name__ == "__main__":
    run(main())
