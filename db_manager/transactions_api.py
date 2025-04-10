
from intasend import APIService
from dotenv import load_dotenv
import os ,json
from db_manager.transactions import TransferManager
from  pathlib import Path
from utils.logger import LOG


load_dotenv()

test = True

if not  os.getenv('SIMULATE_TRANSFERS','false').lower() == 'true':
    
    test= False
    PUBLISHABLE_KEY = os.getenv("PUB_KEY")
    SECRET_KEY = os.getenv("SECRET_KEY")

else:

    PUBLISHABLE_KEY = os.getenv("SANDBOX_PUBLISHABLE_KEY")
    SECRET_KEY = os.getenv("SANDBOX_SECRET_KEY")



def save(filepath ,data):
    with open(filepath ,'w') as file:
        json.dump(data , file ,indent=4)

def read_json(filepath):
    with open(filepath ,'r') as file:
        return json.load(file)

def retrieve_individual_transfer_data(transaction_data):
    status_code = transaction_data['status_code']
    request_reference_id = transaction_data['request_reference_id']
    amount = transaction_data['amount']
    charge = transaction_data.get('charge',0)

    info = {
        'status_code':status_code,
        'amount':amount,
        'recipient_account':transaction_data['account'],
        'recipient_name':transaction_data['name'],
        'request_reference_id':request_reference_id,
        'charges':charge
    }
    return info


def retrieve_batch_data(response):
    tracking_id=response['tracking_id']
    status_code = response['status_code']
    batch_data = {
        'tracking_id':tracking_id,
        'status_code':status_code,
        'total_amount':response['total_amount'],
        'number_of_transactions':response['transactions_count'],
        'actual_charges':response['charge_estimate'],
        'approved': False
    }
    return batch_data
    

class TransactionApi:

    def __init__(self):
        
        self.services = APIService(
            token = SECRET_KEY,
            publishable_key = PUBLISHABLE_KEY,
            test = test
        )
        self.transfer_manager = TransferManager()

        self.pending_approval_dir = Path("UN-APPROVED")

        self.pending_approval_dir.mkdir(parents = True , exist_ok = True)

        self.logger = LOG

    def carry_out_transaction(self,needed_transactions,requires_approval = 'YES'):
        transactions = [{'name':name,'account':phone ,'amount':amount} for name ,phone,amount in needed_transactions]

        response = self.services.transfer.mpesa(
            currency='KES' ,transactions=transactions ,requires_approval=requires_approval

        )
        return response

    def approve_transfer(self,response):
        app = self.services.transfer.approve(response)
        return app

    def check_status(self,reference_id):
        return self.services.transfer.status(reference_id)


    #1. initiate bulk transfer
    def execute_transfer(self, transactions, requires_approval='YES'):
        """

        """
        response = self.carry_out_transaction(
            needed_transactions=transactions,
            requires_approval=requires_approval
        )

        if requires_approval =="YES":
            file_path = (self.pending_approval_dir/response['tracking_id']).with_suffix(".json")
            print(file_path)

        self.process_transfer_step(
            response=response,
            filename=file_path
        )

        return response
    

    def get_pending_approval(self):
        """
          [print(i) for i in api.transfer_manager.query_batched_transer({'status_code':('ge',"BP103")})]
        """
        return self.transfer_manager.query_batched_transer(
            conditions={'status_code':('eq','BP103')}
        )

    def get_approval_pendig_transfers(self ,bath_id):

        self.logger.api_logger.debug("Loading pendng to be approved transfers ")
        pending_file = (self.pending_approval_dir/bath_id).with_suffix(".json")
        if not pending_file.exists():
            self.logger.api_logger.debug(f"Pending file {pending_file} does not exist ")
            return None
        pending_file = read_json(pending_file)
        return pending_file
    
    #2. approve transaction
    def manage_approval(self,response):
        self.logger.api_logger.debug('approving transfer .')
        approved = self.approve_transfer(response)
        
        self.process_transfer_step(
            response=approved,
            filename='approved.json'
        )
        return approved['tracking_id']
        
    #3. check status
    def check_and_update_batch_status(self,tracking_id):
        self.logger.api_logger.debug("Checking transfer id status ..")

        try:
            status = self.check_status(
                reference_id= tracking_id,
            )
        except Exception as e:
            LOG.get_payment_logger.error(f"{tracking_id} failes to update: error {str(e)}")
            return None
            
        self.process_transfer_step(
            response=status,
            filename=f'checked_status_{tracking_id}.json'
        )
        return True


    @staticmethod
    def process_transfer_step(response, filename):
        batch_data = retrieve_batch_data(response)
        individual_data = [retrieve_individual_transfer_data(t) for t in response['transactions']]
        
        TransferManager.record_transfers(
            bulk_transaction_data=batch_data,
            individual_transaction_data=individual_data
        )
        
        save(filename, response)
        return response

