
from flask import Blueprint ,request ,jsonify  ,render_template
from flask import url_for ,redirect
from db_manager.transactions_api import TransactionApi
from utils.logger import api_error_logger ,LOG
import os
from functools import wraps
from datetime import datetime ,timedelta
from pathlib import Path

API_TOKEN = os.getenv("API_TOKEN")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

transfer_bp = Blueprint('transfer',__name__ ,url_prefix='/transfers' 
                        ,template_folder=Path('templates/transfer/').absolute())

trans_db  = TransactionApi()
IN_DEVELOPMENT = os.getenv("IN_DEVELOPMENT",'false').lower() == "true"
DOCS_ACCESS_TOKEN = os.getenv("DOCS_ACCESS_TOKEN") if not IN_DEVELOPMENT else "test"


# =================
# HELPER FUNCTIONS
# =================

def extract_request_data(records):
    name = records.get("name" ,None)
    phone = records.get('phone',None)
    amount = records.get('amount',None)
    return name ,phone ,amount

def get_api_key(key = "Authorization"):
    api_key = request.headers.get(key ,"None None")
    api_key = api_key.split(" ")[1] if api_key else None
    return api_key



def token_required(admin=False):
    """
    Decorator to enforce token-based authentication.
    Set `admin=True` to require ADMIN_TOKEN.
    """
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            token = get_api_key()

            if not token:
                return jsonify({'message': 'Unauthorized'}), 403

            if admin:
                if token != ADMIN_TOKEN:
                    return jsonify({'message': 'Unauthorized'}), 403
            else:
                if token not in [API_TOKEN, ADMIN_TOKEN]: 
                    return jsonify({'message': 'Unauthorized'}), 403

            return func(*args, **kwargs)
        return wrapped
    return decorator


def content_type_is_json(func):
    @wraps(func)
    def decorated(*args ,**kwargs):
        if request.is_json:
            return func(*args ,**kwargs)
        else:
             return jsonify({
                    "message": "failed",
                    "data": "Request needs to be of content type json"
                }), 400 
    return decorated


def verified_for_docs(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        args = request.args.get("access_token" ,None)
        
        if args and args == DOCS_ACCESS_TOKEN :
            return func(*args ,**kwargs)
        if IN_DEVELOPMENT:
            return jsonify({
                "message":"access_token is required to view this page",
                "token":args
            })
        
        return redirect(
            url_for('transfer.home' ,_external=True)
        )
    return decorated


# =================
# HOME DECLARATION
# =================


@transfer_bp.route("/" ,methods = ['GET'])
def home(*args , **kwargs):
    access_token = request.args.get('token' ,None)
    return render_template("home.html" ,token=access_token)
     
# @transfer_bp.route("/docs")
# # @verified_for_docs
# # @api_error_logger(logger=LOG.api_logger , in_development=IN_DEVELOPMENT)
# def docs(*args , **kwargs):
#     access_token = request.args.get('access_token' ,None)
#     # text= render_template("docs.html" , token =access_token )

#     file_path2 = Path(".")/'templates/transfer/docs.md'
 
    
#     with open(file_path2 , 'r') as file:
#         md_texxt = file.read()
    
#     return render_template('docs.html' ,docs=md_texxt)
   
from pathlib import Path
import markdown  # <-- Make sure you have this installed

@transfer_bp.route("/docs")
def docs(*args, **kwargs):
    access_token = request.args.get('access_token', None)

    file_path = Path("templates/transfer/docs.md")

    with open(file_path, 'r') as file:
        md_text = file.read()

    # Convert Markdown to HTML
    html_content = markdown.markdown(md_text, extensions=['fenced_code', 'codehilite'])

    return render_template('docs2.html', docs=html_content)


# =======================
# ENDPOINTS FOR API CALLS
# =======================


@transfer_bp.route("/initiate/single" ,methods = ['POST'])
@token_required()
@content_type_is_json
@api_error_logger(logger=LOG.get_payment_logger)
def transfer_home():
    """
    Initiate as single transfer
    request needs to be json
    records are in the format
    {
        "name":"string",
        "phone":"string",
        "amount":1000
    }
    """
    data = request.get_json()
    records = data.get("records" ,None)

    if not records: 
        return jsonify({"message":"records is required" }) ,400
    
    name , phone ,amount = extract_request_data(records)
    requires_approval = data.get("requires_approval" ,"YES")

    if not all([records ,name ,phone ,amount]):
        return jsonify({"message":"records should contain name:{} , phone:{} and amount:{}".format(
            name ,phone ,amount)}) ,400
    
    response = trans_db.execute_transfer(
        transactions= [(name ,phone ,amount)],
        requires_approval=requires_approval
    )

    return jsonify(
        {"message":"success",
         'data':"transfer initiated awaiting approval" if requires_approval == "YES" else "transfer initiated",
         'tracking_id':response['tracking_id']}
    ) ,200


@transfer_bp.route("/initiate/bulk" ,methods = ['POST'])
@token_required(True)
@content_type_is_json
@api_error_logger(logger=LOG.get_payment_logger)
def initiate_bulk():

    """
    Initiate a bulk transfer
    request needs to be json
    records are in the format
    -   [
            {
                "name":"string",
                "phone":"string",
                "amount":1000
            },
            {
                "name":"string",
                "phone":"string",
                "amount":1000
            }, ..
        ]
    """

    data = request.get_json()
    records = data.get("records" ,None)
    if not records: 
        return jsonify({"message":"records is required" }) ,400
    if not isinstance(records ,list):
        return jsonify ({"message":"records should be a list" }) ,400
    if not all(isinstance(i ,dict) for i in records):
        return jsonify({"message":"records should be a list of dictionaries" }) ,400
    
    transactions = [extract_request_data(record) for record in records]
    transactions = [i for i in transactions if all(i)]

    if not transactions:   
        return jsonify(
            {"message":"Invalid format for records"}
        ) ,400
    requires_approval = data.get("requires_approval" ,"YES")
    response = trans_db.execute_transfer(
        transactions=transactions,
        requires_approval=requires_approval
    )    
    return jsonify({
        "message":"success",
        "tracking_id":response['tracking_id'],
    }) , 200



@transfer_bp.route("/approvals-pending")
@token_required(True)
@api_error_logger(logger=LOG.get_payment_logger)
def get_pending_approvals():
    """Retrieve all transfers awaiting approval

    returns a list of dict format for pending records
    [
        {
            "tracking_id":"string",
            "status_code":"string",
            "total_amount": 1000,
            'number_transaction':10,
            "created_at": datetime.datetime.strftime(self.created_at ,"%Y-%m-%d %H:%M:%S")
        }
    ]
    """
    batches = trans_db.get_pending_approval()

    parsed_batches = list(i.to_dict() for i in batches) if batches else []

    return jsonify(parsed_batches) ,200


@transfer_bp.route("/approve" ,methods=['POST'])
@token_required(True)
@content_type_is_json
@api_error_logger(logger=LOG.get_payment_logger)
def approve_trasfer_batch():

    """
    Approve initiated batch trasfers 
    whose requires approval parameter was set to `YES
    {
        "batch_id":"string"
    }
    """
   
    data = request.get_json()
    batch_id = data.get("batch_id" ,None)
    if not batch_id:
        return jsonify({"message":"batch_id is required" }) ,400
    if not isinstance(batch_id ,str):  
        return jsonify({"message":"batch_id should be a string" }) ,400
    if not batch_id.strip():
        return jsonify({"message":"batch_id should not be empty" }) ,400

    response = trans_db.get_approval_pendig_transfers(batch_id)
    if not response:
        return jsonify({"message":"batch_id does not exist" }) ,400    

    trans_db.manage_approval(response)
    return jsonify(
        {"message":"batch_id is approved",
         "status_code":response['status_code'],}
    ) , 200




@transfer_bp.route("/update" ,methods=['POST'])
@token_required(True)
@content_type_is_json
@api_error_logger(logger=LOG.get_payment_logger)
def update_batch():

    try:
        tracking_id = request.get_json().get("tracking_id" ,None)
    except Exception as e:
        return jsonify({"message":"error" ,'data':"Invalid data format"}) , 400


    if not tracking_id:
         return jsonify({"message":"tracking_id is required" }) ,400

    
    response = trans_db.check_and_update_batch_status(tracking_id)

    if response:
        return jsonify({"message":"success" ,'data':"updated the status"})  , 200
    else:
        return jsonify({"message":"failed" ,'data':"Update for failed"}) , 400




@transfer_bp.route("/check-status" ,methods = ['POST'])
@token_required(True)
@api_error_logger(logger=LOG.get_payment_logger)
def check_status():

    """
    Check status for an initiated batch transfer
    {
        "tracking_id":"string"
    }
  
    """


    data = request.get_json()
    tracking_id = data.get("tracking_id" ,None)
    if not tracking_id:
        return jsonify({"message":"tracking_id is required" }) ,400
    if not isinstance(tracking_id ,str):
        return jsonify({"message":"tracking_id should be a string" }) ,400
    if not tracking_id.strip(): 
        return jsonify({
            "message":"tracking_id should not be empty" }) ,400
    
    batch_transfer = trans_db.transfer_manager.query_batched_transer(
        {"tracking_id":("eq" ,tracking_id)}
    )
    
    if not batch_transfer:
        return jsonify({"message":"tracking_id does not exist" }) ,400
    
    batch_data = [i.to_dict() for i in batch_transfer]
    return jsonify(
        {"message":"success",
         "data":batch_data}
    ) , 200


@transfer_bp.route("/transfer-status")
@token_required(True)
@api_error_logger(logger=LOG.get_payment_logger)
def individual_tranfer_status():
    """
    check the status of an individual transfer
    {
        "reference_id":"string"
    }

    """

    reference_id = request.get_json().get("reference_id" ,None)
    if not reference_id:
        return jsonify({"message":"reference_id is required" }) ,400
    
    if not reference_id.strip():
        return jsonify({"message":"reference_id should not be empty" }) ,400
    if not isinstance(reference_id ,str):   
        return jsonify({"message":"reference_id should be a string" }) ,400
    
    transfer_data = trans_db.transfer_manager.query_individual_transfer(
        {"request_reference_id":("eq" ,reference_id)}
    )
    if not transfer_data:
        return jsonify({"message":"reference_id does not exist" }) ,400
    transfer_data = [i.to_dict() for i in transfer_data]
    return jsonify(
        {"message":"success",
         "data":transfer_data}
    ) , 200




@transfer_bp.route("/transactions" ,methods=['POST'])
@token_required(True)
@api_error_logger(logger=LOG.get_payment_logger)
def retrieve_batch_components():
    """ Retrieve transaction asociated to a certain batch transfer

        batch_id need to be an integer ie from the id column of the batched transfers
    """
    batch_id = request.get_json().get("tracking_id" ,None)

    if not batch_id:
        return jsonify(
            {"message":"tracking_id is needed"} 

            ) , 400

    data = trans_db.transfer_manager.get_batch_transfer_children(batch_id)
    return jsonify(
        {"message":"success",
        "data":data}
        )



@transfer_bp.route("/inspect" , methods=['POST'])
@token_required(True)
@content_type_is_json
@api_error_logger(logger = LOG.get_payment_logger)
def inspect():

    
    try:
        data = request.get_json()
    except Exception as e:
        return jsonify({"message":"error" ,'data':str(e)}) , 400


    check_date = data.get('date' ,None)

    if not check_date:
        check_date =  datetime.now().date()
    else:
        try:
            check_date = datetime.strptime(check_date ,"%Y-%m-%d").date()
        except Exception as e:
            return jsonify({"message":"failed" ,"data": "Invalid date format. Use YYYY-MM-DD."}), 400

    logic = data.get('logic' ,'eq') # ge ,eq , le
    interval = data.get("interval",30) if logic !='eq' else 0 # the number of day to go past or foward

    duration = timedelta(days = interval)

    print("the date is " , check_date)
    data = trans_db.transfer_manager.grab_all_transfers([(check_date ,logic)])
    if not data:
        data = "No data found"

    return jsonify({"message":"success" ,"data":data})
        


@transfer_bp.route("/fetch-statuses")
@token_required(True)
@api_error_logger(logger=LOG.get_payment_logger , in_development=IN_DEVELOPMENT) 
def get_status():

    data= trans_db.transfer_manager.get_status()
    if not data:
        return jsonify({"message":"failed" ,"data":"No data found"})
    data =[{"code":i.name ,

            "description":i.value[1]}for i in data]
    return jsonify({"message":"success" , 'data':data})   





