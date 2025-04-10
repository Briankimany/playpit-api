
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, DECIMAL, ForeignKey
)

from enum import Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime
from models.base import Base
from models.init_db import engine 



class PaymentRequest(Base):
    __tablename__ = 'payment_requests'

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(String(50), nullable=False)
    phone = Column(String(15), nullable=False)  # Changed to String for phone
    amount = Column(Integer, nullable=False)
    date = Column(DateTime, nullable=False)  # Changed to DateTime
    order_id = Column(String(50), nullable=False)
    status = Column(String, default='WAITING')

    def __repr__(self):
        return (f"PaymentRequest(id={self.id}, phone={self.phone}, "
                f"amount={self.amount}, order_id={self.order_id}, "
                f"invoice_id={self.invoice_id}, status={self.status})")
    

    def __str__(self):
        return self.__repr__()
    

class BatchedTransfer(Base):
    __tablename__ = 'batched_transactions'

    id = Column(Integer, primary_key=True)
    tracking_id = Column(String, unique=True, nullable=False)
    status_code = Column(String,nullable=False)
    total_amount = Column(DECIMAL,nullable=False)
    number_of_transactions = Column(Integer ,nullable = False)
    actual_charges = Column(DECIMAL ,nullable = False)
    approved = Column(Boolean ,nullable = True)
 
    individual_transactions = relationship("IndividualTransfer", back_populates="batch")

    def __repr__(self):
        return (
            f"<BatchedTransfer(id={self.id}, tracking_id='{self.tracking_id}', "
            f"status_code='{self.status_code}', total_amount={self.total_amount}, "
            f"transactions={self.number_of_transactions}, approved={self.approved}, "
            f"created_at='{self.created_at}')>"
        )
    
    def __str__(self):
        return self.__repr__()
    
    def to_dict(self ,children=False):
        """
        Returns a bathced record in form of a dict
        {
            "tracking_id":self.tracking_id,
            "status_code":self.status_code,
            "total_amount": self.total_amount,
            'number_transaction':self.number_of_transactions,
            "created_at": datetime.datetime.strftime(self.created_at ,"%Y-%m-%d %H:%M:%S")
        }
        """
        data= {
            "tracking_id":self.tracking_id,
            "status_code":self.status_code,
            "total_amount": self.total_amount,
            'number_transaction':self.number_of_transactions,
            "created_at": datetime.datetime.strftime(self.created_at ,"%Y-%m-%d %H:%M:%S")
        }
        if children:
            data.update({"transfers":[i.to_dict() for i in self.individual_transactions]})

        return data


class IndividualTransfer(Base):
    __tablename__ = 'individual_transactions'

    id = Column(Integer, primary_key=True)
    batched_id = Column(Integer, ForeignKey('batched_transactions.id') ,nullable = False)
    status_code = Column(String ,nullable = False)                                                                       
    amount = Column(DECIMAL ,nullable = False)
    charges = Column(DECIMAL ,nullable = False) 

    recipient_account = Column(String ,nullable = False)
    recipient_name = Column(String ,nullable=False)
    request_reference_id = Column(String ,nullable = False)
    

    
    batch = relationship("BatchedTransfer", back_populates="individual_transactions")

    def __repr__(self):
        return (
            f"<IndividualTransfer(id={self.id}, batched_id={self.batched_id}, "
            f"status_code='{self.status_code}', amount={self.amount}, "
            f"recipient='{self.recipient_name}', phone='{self.recipient_account}', "
            f"reference='{self.request_reference_id}')>"
        )
    
    def __str__(self):
        return self.__repr__()
    
    def to_dict(self):
        """
        returns a dictionary representation of the object
        {
            'name':self.recipient_name,
            'account': self.recipient_account,
            'amount':self.amount,
            'reference_id': self.request_reference_id,
 
            'status_code':self.status_code,
            'charges':self.charges
            'created_at': datetime.datetime.strftime(self.created_at ,"%Y-%m-%d %H:%M:%S")
        }
        """
        return {
            'name':self.recipient_name,
            'account': self.recipient_account,
            'amount':self.amount,
            'reference_id': self.request_reference_id,
          
            'status_code':self.status_code,
            'charges':self.charges,
            'created_at': datetime.datetime.strftime(self.created_at ,"%Y-%m-%d %H:%M:%S")  
        }



class User(Base):

    __tablename__ = "users"
    id = Column(Integer  , autoincrement=True , primary_key= True)
    first_name = Column(String(20) ,nullable = False)
    second_name = Column(String(20) ,nullable= False)
    email = Column(String(50) ,nullable = False)
    password = Column(String(30))



class Token(Base):
    __tablename__ = "tokens"
    id = Column(Integer ,autoincrement=True , primary_key=True)
    token = Column(String(50) ,nullable = False)
    valid = Column(Boolean,nullable = False)
    expires_at = Column(DateTime ,nullable = False)

    def to_dict(self):
        return {
            'token':self.token,
            'is_valid':self.valid
        }

    def __str__(self):
        return f"tkn=({self.token} ,expires = {self.expires_at})"

    def __repr__(self):
        return self.__str__()


def create_db():
    """
    Create the database and tables if they don't exist.
    """
    Base.metadata.create_all(engine)
    print("Database and tables created successfully.")
    return True


if __name__ == "__main__":
    Base.metadata.create_all(engine)