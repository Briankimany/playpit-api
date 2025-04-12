
from dotenv import load_dotenv
import os
from pathlib import Path
from utils.logger import LOG

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
IN_DEVELOPMENT = os.getenv("MY_IN_DEVELOPMENT", 'true').lower() == 'true'
print("IN_DEVELOPMENT", IN_DEVELOPMENT)
SIMULATE_TRANSFERS = os.getenv("SIMULATE_TRANSFERS", "true").lower() == 'true'


test = True
if not IN_DEVELOPMENT:
    LOG.api_logger.info("Loading live enviroment keys")

    test= False
    PUBLISHABLE_KEY = os.getenv("PUB_KEY")
    SECRET_KEY = os.getenv("SECRET_KEY")

else:
    LOG.api_logger.info("loading sandbox keys")
    
    PUBLISHABLE_KEY = os.getenv("SANDBOX_PUBLISHABLE_KEY")
    SECRET_KEY = os.getenv("SANDBOX_SECRET_KEY")



print(f"in the environ file {IN_DEVELOPMENT}")