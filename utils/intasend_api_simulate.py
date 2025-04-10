import requests
from config.config import ConfigClass
from utils.initialize_logger import init_logger
from config.config import ConfigClass


log_file = ConfigClass().LOG_DIR / "REMOTE PAYMENTS" / "SIMULATED LOGS.LOG"
logger = init_logger(log_file=log_file, name=__name__)

def make_delayed_payment_request(url, username, content_ids, orderid , status):
    payload = {
        "user_name": username,
        "ids": content_ids,
        "orderid": orderid,
        'status':status
    }
    response = requests.post(url, json=payload)
    return response

def simulate_status(invoice_id, elapsed_time):
    if elapsed_time >= 3:
        payment_status = 'COMPLETE'
        reason = 'Transaction completed'

    else:
        payment_status = 'PENDING'
        reason = 'Transaction pending'
    return {
        'invoice': {
            'invoice_id': invoice_id,
            'state': payment_status,
            'failed_reason': reason
        }
    }