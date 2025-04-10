import requests , time ,os ,json
from requests.adapters import HTTPAdapter
from dotenv import load_dotenv


from config.config import ConfigClass
from utils.initialize_logger import init_logger


load_dotenv()
PUB_KEY = os.getenv('PUB_KEY')
PRIVATE_KEY = os.getenv('SECRET_KEY')

SERVER_URL = "https://playpit.pythonanywhere.com"
PAY_REMOTE_ADDRES = SERVER_URL + "/pay"

REMOTE_CHECK_STATUS_URL = SERVER_URL + "/check-status"
INTERFACE_IP = "20.12.220.138"
HEADERS = {'Content-Type': 'application/json'}
STATUS_URL = SERVER_URL + "/status"

log_file = ConfigClass().LOG_DIR / "REMOTE PAYMENTS" / "REMOTE INTASEND_API.LOG"
logger = init_logger(log_file=log_file, name="PAY")


class BindableAdapter(HTTPAdapter):
    def __init__(self, source_ip ,**kwargs):
        self.source_ip =source_ip
        super().__init__(**kwargs)
    def init_poolmanager(self,*args ,**kwargs):
        kwargs['source_address']= (self.source_ip , 0)
        return super().init_poolmanager(*args , **kwargs)
def get_with_interface(url , interface , data = None , headers = None):
    session = requests.session()
    session.mount("http://",BindableAdapter(interface))
    session.mount("https://", BindableAdapter(interface))
    return session.get(url , data =  json.dumps(data) , headers=headers)

def post_with_interface(url, interface, data=None, headers=None):
    session = requests.Session()
    session.mount("http://", BindableAdapter(interface))
    session.mount("https://", BindableAdapter(interface))

    response = session.post(url, json= data, headers=headers)
    return response


def check_internet_access(url='http://www.google.com', timeout=5):
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except requests.ConnectionError:
        return False
    except requests.Timeout:
        return False


def make_delayed_payment_request(url, username, content_ids, orderid , status):
    payload = {
        "user_name": username,
        "ids": content_ids,
        "orderid": orderid,
        'status':status
    }
    response = requests.post(url, json=payload)
    return response

def check_payment_status_local(session):
    try:
        logger.info("**"*35)
        logger.info("check_payment_status procces started")

        response = session.get("response")
        username = session.get('user_name')  
        content_ids = session.get("ids")      
        orderid = session.get('orderid')     
        start_sleep_time = 30
        for i in range(7):
            invoice_id = response['invoice']['invoice_id']

            remote_status =get_with_interface(f"{REMOTE_CHECK_STATUS_URL}/{invoice_id}", INTERFACE_IP ,
                                           data = {"SIMULATE":False , 'MAXRETRIES':i} , headers=HEADERS).json()


            status = remote_status.get('status')
            STAGE = status['invoice']['state']
            reason = status['invoice']['failed_reason']



            if STAGE == 'COMPLETE':
                response = make_delayed_payment_request(ConfigClass().DELAYED_PAYMENT_ADDRESS, username=username,
                                                         content_ids=content_ids, orderid=orderid , status='VERIFIED')

                logger.info(f"Success: Order {orderid} completed. Updating URL: {ConfigClass().DELAYED_PAYMENT_ADDRESS}.")
                logger.info(f"Server response: {response.status_code}, Content: {response.json()}")

                return True
            
            if STAGE == 'FAILED':
                logger.info(f"Failed: {invoice_id}. Updating URL: {ConfigClass().DELAYED_PAYMENT_ADDRESS}.")
                response = make_delayed_payment_request(ConfigClass().DELAYED_PAYMENT_ADDRESS, username=username, content_ids=content_ids, orderid=orderid , status='DENIED')
                return False
            
            elif  STAGE == 'CANCELED':
                logger.info(f"Canceled: {invoice_id}. Updating URL: {ConfigClass().DELAYED_PAYMENT_ADDRESS}.")
                response = make_delayed_payment_request(ConfigClass().DELAYED_PAYMENT_ADDRESS, username=username, content_ids=content_ids, orderid=orderid , status='DENIED')
            else:
               logger.info(f"Invoice {invoice_id}: Status: {STAGE}, Reason: {reason}")

            start_sleep_time*=.6
            time.sleep(start_sleep_time)

        logger.info(f"Transaction not completed: Reason: {reason}, Invoice ID: {invoice_id}")
        logger.info("**"*35)
    except Exception as e:
        logger.error(f"In check payment status {e}")

