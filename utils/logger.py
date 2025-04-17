
import logging
from pathlib import Path
import os 
from dotenv import load_dotenv
from functools import wraps
from flask import jsonify

load_dotenv()

def init_logger(log_file: Path, name:str):
    
    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_file)  
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )

    logger = logging.getLogger(name)
    logger.handlers.clear()
    logger.setLevel(getattr(logging, os.getenv("LOGGING_LEVEL",'DEBUG').upper()))
    

    logger.addHandler(file_handler)
    
    return logger

class LOG:
    LOG_DIR = Path(os.getenv("LOG_DIR",'LOGS'))

    db_logger = init_logger(LOG_DIR/'database.log','database')
    api_logger = init_logger(LOG_DIR/'payment_api.log' ,'get-payment-api')
    get_payment_logger = init_logger(LOG_DIR/'transfer-requests.log' ,'transfer-request')
    intasend_logger = init_logger(LOG_DIR/"intasend-request.log" ,'intasend-req')




def db_error_logger(logger:LOG  ,raise_exception =False):
    def wrapper(func):
        @wraps(func)
        def wrapper_func(*args,**kwargs):
            try:
                return func(*args ,**kwargs)
            except Exception as e:
                message = f" error {str(e)} from {func.__name__} ,args=({args}) ,kwargs=({kwargs})"
                logger.error(message)
                if raise_exception:
                    raise Exception(f"Error {e}")
                return None
        return wrapper_func
    return wrapper


def api_error_logger(logger:LOG ,in_development=True):
    def wrapper(func):
        @wraps(func)
        def wrapper_func(*args,**kwargs):
            try:
                return func(*args ,**kwargs)
            except Exception as e:
                message = f" error {str(e)} from {func.__name__} ,args=({args}) ,kwargs=({kwargs})"
                logger.error(message)

                if in_development:
                    return jsonify({"message":'error' ,'error':str(e)}) ,500
                return jsonify({"message":"error",'error':"contact support"}) ,500

        return wrapper_func
    return wrapper




if __name__ == "__main__":
    pass