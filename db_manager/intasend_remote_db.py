
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from models.transfers import PaymentRequest
from models.init_db import engine 
from utils.logger import LOG

Session = sessionmaker(bind=engine)



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
