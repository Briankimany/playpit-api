import logging
from pathlib import Path
import os 
from dotenv import load_dotenv
from functools import wraps

load_dotenv()


def init_logger(log_file:Path , name = __name__):
    """
    Initializes a logger that writes log messages to the specified log file.

    Args:
        log_file (str): The file path where the log messages will be saved.

    Returns:
        logging.Logger: The configured logger instance.
    """

    log_file.parent.mkdir(parents=True , exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG) 

  
    file_handler = logging.FileHandler(log_file, mode='a')  
    file_handler.setLevel(logging.DEBUG) 

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger

class LOG:
    LOG_DIR = Path(os.getenv("LOG_DIR",'LOGS'))
    payment_api = init_logger(LOG_DIR/'payment_api.log')
    db_logger = init_logger(LOG_DIR/'db.logs')


def db_error_logger(logger:LOG):
    def wrapper(func):
        @wraps
        def wrapper_func(*args,**kwargs):
            try:
                return func(*args ,**kwargs)
            except Exception as e:
                message = f" error from {func.__name__} ,args=({args}) ,kwargs=({kwargs})"
                logger.error(message)
        return wrapper_func
    return wrapper
