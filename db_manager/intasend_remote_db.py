
from sqlalchemy.orm import sessionmaker ,scoped_session
from datetime import datetime

from models.transfers import PaymentRequest ,User
from models.init_db import engine 
from utils.logger import LOG
from contextlib import contextmanager

Session = sessionmaker(bind=engine)


class UserManger:

    @classmethod
    @contextmanager
    def _session_scope(commit =False):
        db_session =  Session()
        try:
            yield db_session

            if commit:
                 db_session.commit()
            db_session.close()

        except ValueError as e:
            LOG.db_logger.error(f"Error occured during db interaction the error {e}")
            db_session.rollback()
            return None
    
    @classmethod
    def add_user(cls , **kwargs):
        user = User(**kwargs)
        with cls._session_scope() as db_session:

            pre_user = db_session.query(User).filter(User.email == user.email).first()

            if pre_user:
                LOG.db_logger.info(f"attempted to create user <{user}>")
                return False
            
            LOG.db_logger.info(f"created user <{user}>")
            db_session.add(user)
            db_session.commit()

        return True
    
    @classmethod
    def verify_user(cls ,email ,password):
        with cls._session_scope() as db_session:
            user = db_session.query(User).filter(User.email == email).first()
            LOG.db_logger.debug(f"Trrying to Verifying user: {user}")
            if not user:
                LOG.db_logger.info(f"User not found: {email}")
                return None
            
            return user.verify_password(password)
        

def add_payment_request(phone, amount, order_id, invoice_id):
    date = datetime.now()
    with Session() as session:  
        invoice = session.query(PaymentRequest).filter_by(invoice_id=invoice_id).first()
        if invoice:
            return  
        else:
            LOG.db_logger.info("Adding new payment request to the database.")
            LOG.db_logger.debug(f"Adding payment request: Phone={phone}, Amount={amount}, Order ID={order_id}, Invoice ID={invoice_id}, Date={date}")

            new_request = PaymentRequest(phone=phone, amount=amount, order_id=order_id, invoice_id=invoice_id, date=date)
            session.add(new_request)
            session.commit()

def update_payment_status(invoice_id, status):
    with Session() as session: 
        request = session.query(PaymentRequest).filter_by(invoice_id=invoice_id).first()
        if request:
           
            LOG.db_logger.debug(f"Updating payment status: Invoice ID={invoice_id}, Status={status}")

            request.status = status
            session.commit()
        else:
            log_message = f"No payment request found with that invoice ID {invoice_id}"
            LOG.db_logger.debug(log_message)

def get_payment_status(invoice_id):
    with Session() as session: 
        request = session.query(PaymentRequest).filter_by(invoice_id=invoice_id).first()
        if request:
           
            LOG.db_logger.debug(f"Retrieving payment status: Invoice ID={invoice_id}, Status={request.status}")

            return request.status
        else:
           
            LOG.db_logger.debug(f"No payment request found with that invoice ID {invoice_id}")
            return f"No payment request found with that invoice ID {invoice_id}"
    return None


if __name__ == "__main__":
    pass
