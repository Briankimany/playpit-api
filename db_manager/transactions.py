from models.transfers import BatchedTransfer ,IndividualTransfer
from models.init_db import engine
from sqlalchemy import  func
from sqlalchemy.orm import sessionmaker

from contextlib import contextmanager
from typing import List ,Dict 


from operator import eq ,le ,ge ,lt , gt

from utils.logger import LOG , db_error_logger 
from utils.status_codes import  BatchRequestStatus
from config.config import ConfigClass

config = ConfigClass()




def update_object_attributes(tartget_object ,new_values:dict):
    for key ,value in new_values.items():
        if hasattr(tartget_object ,key):
            setattr(tartget_object,key ,value)
        else:
            LOG.db_logger.warning(f"Potential error got invalid attribute {key}:{value}")
    return tartget_object


class TransferManager:
    Session = sessionmaker(bind = engine)

    mapper = {
            'eq':eq,
            'le':le,
            'ge':ge,
            'gt':gt,
            'lt':lt
        }


    @classmethod
    @contextmanager
    def session_scope(cls,close_session = True ,*args ,**kwargs):
        db_session = cls.Session()
        db_session.expire_on_commit = False
        try:
            yield db_session
        except Exception as e:
            LOG.db_logger.error(f"Error {e} during record args=({args}) ,kwargs=({kwargs})")
            db_session.rollback()
        finally:
            if close_session:
                db_session.close()
        

    @classmethod
    def record_transfers(cls,bulk_transaction_data:Dict ,individual_transaction_data:List[Dict]):
        with cls.session_scope() as db_session:
            bulk_record = db_session.query(BatchedTransfer
                                           ).filter(BatchedTransfer.tracking_id== bulk_transaction_data['tracking_id']
                                                    ).first()
            if not bulk_record:
             
                bulk_record = BatchedTransfer(**bulk_transaction_data)
                db_session.add(bulk_record)
                db_session.commit()
              
                [i.update({"batched_id":bulk_record.id}) for i in individual_transaction_data]
                single_records = [IndividualTransfer(**record) for record in individual_transaction_data]
                db_session.add_all(single_records)
                db_session.commit()
               
            else:
                single_records = db_session.query(IndividualTransfer).filter(IndividualTransfer.batched_id==bulk_record.id).all()
                
                LOG.db_logger.debug(f"updating single transaction status from {single_records[0].status_code}")

                bulk_record=cls.update_batch_record(transaction_id=bulk_record.tracking_id ,
                                                    new_values=bulk_transaction_data
                                                    ,db_session=db_session)
                
                single_records=[cls.update_individual_transaction(record.request_reference_id ,
                                                                  db_session = db_session,
                                                                  new_values=individual_transaction_data[index]) for index,record in enumerate(single_records)]

                db_session.commit()

            LOG.db_logger.debug(str(bulk_record))
            LOG.db_logger.debug(str(single_records[0]))

      
        
    
    @db_error_logger(logger=LOG.db_logger)
    @staticmethod
    def update_batch_record(transaction_id:str,new_values:Dict,db_session):

        batch_record = db_session.query(BatchedTransfer).filter( BatchedTransfer.tracking_id == transaction_id ).first()
        batch_record = update_object_attributes(batch_record,new_values)
        return batch_record
    
        
    @db_error_logger(logger=LOG.db_logger)
    @staticmethod
    def update_individual_transaction(reference_id ,new_values,db_session):
        transaction = db_session.query(IndividualTransfer).filter(
                IndividualTransfer.request_reference_id == reference_id
                ).first()
            
        transaction = update_object_attributes(
            tartget_object=transaction,
            new_values=new_values
        )
        return transaction
    

    @classmethod
    def get_pending_approval_transactions(cls):

        with cls.session_scope() as db_session:
            pending_bulk = db_session.query(
                BatchedTransfer
            ).filter(
                BatchedTransfer.approved == False
            ).all()

            return pending_bulk
        

    @classmethod
    def query_batched_transer(cls,conditions:dict):

        all_conditions = []

        for key , (comparitor_str , value) in conditions.items():
            condition = cls.mapper[comparitor_str](getattr(BatchedTransfer ,key),value)
            all_conditions.append(condition)

       
        with cls.session_scope() as db_session:
            record = db_session.query(BatchedTransfer).filter(
                *all_conditions
            ).all()
            if not record:
                return None
            return record
        
    @classmethod
    def query_individual_transfer(cls ,conditions:dict):
        all_conditions = []

        for key , (comparitor_str , value) in conditions.items():
            condition = cls.mapper[comparitor_str](getattr(IndividualTransfer ,key),value)
            all_conditions.append(condition)

        with cls.session_scope(close_session=False) as db_session:
            record = db_session.query(IndividualTransfer).filter(*all_conditions).all()
            return record ,db_session
        

    @classmethod
    def get_batch_transfer_children(cls ,tracking_id):

        with cls.session_scope() as db_session:
            record = db_session.query(
                    BatchedTransfer).filter(BatchedTransfer.tracking_id == tracking_id).first()

            return [i.to_dict() for i in record.individual_transactions]

    @classmethod
    def grab_all_transfers(cls ,conditions):
        conditions  = [cls.mapper[logic](func.date(BatchedTransfer.created_at) ,date) for date , logic in conditions]
        
        with cls.session_scope() as db_session:
            records = db_session.query.filter(*conditions).all()
            return [i.to_dict(True) for i in records]
        

    @classmethod
    def  get_status(cls):

        with cls.session_scope() as db_session:
            data = db_session.query(BatchedTransfer.status_code).distinct().all()
            status_codes = [i[0] for i in data]

            return [getattr(BatchRequestStatus ,i) for i in status_codes]
        
    
