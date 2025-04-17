
from dotenv import load_dotenv
import os
from pathlib import Path
from utils.logger import LOG

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
IN_DEVELOPMENT = os.getenv("MY_IN_DEVELOPMENT", 'true').lower() == 'true'

LOG.api_logger.info("IN_DEVELOPMENT: {}".format(IN_DEVELOPMENT))

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



class StatusCodes:
    WAITING = ["TP101", "TP102", "TF104", "TR109"]

    CANCELED = ["TF10"]

    SUCCESS = ["TS100" ,'TF103']

    CONTACT_ADMIN = ["TP105", "TC108", "TF106"]

    TERMINAL_STATUS_CODES = CANCELED + SUCCESS +CONTACT_ADMIN


API_TOKEN = os.getenv("API_TOKEN")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")



DOCS_ACCESS_TOKEN = os.getenv("DOCS_ACCESS_TOKEN") if not IN_DEVELOPMENT else "test"
