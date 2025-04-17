from flask import Flask, request, jsonify, session 
from intasend import APIService
from flask import render_template, redirect
import os


import time
from functools import wraps
from flask_cors import CORS

from utils.intasend_api_simulate import simulate_status
from db_manager.intasend_remote_db import update_payment_status , add_payment_request , get_payment_status
from pathlib import Path


from views.transfer_api import transfer_bp ,token_required ,content_type_is_json
from utils.logger import LOG , api_error_logger
from models.transfers import create_db
from utils.environ_variables import IN_DEVELOPMENT ,PUBLISHABLE_KEY,SECRET_KEY ,test ,SIMULATE_TRANSFERS
from db_manager.intasend_remote_db import UserManger


create_db()
current_dir = Path(".")

app = Flask(__name__ ,template_folder = (current_dir/'templates').absolute(),
            static_folder=(current_dir/'static').absolute()
            )


CORS(app)

app.secret_key= os.getenv('FLASK_SECRET_KEY')
app.config['EXECUTOR_TYPE'] = 'threads'
app.config['EXECUTOR_PROPAGATE_EXCEPTIONS'] = True

app.register_blueprint(transfer_bp)


def initiate_intasend_service():
    return APIService(token=SECRET_KEY, publishable_key=PUBLISHABLE_KEY ,test = test)    


def make_request_to_instasend(pub, key, phone: int, amount,orderid ,description="Purchase" , simulate=False ,test = test):
    LOG.api_logger.info("__"*50)
    LOG.api_logger.info(f"Initiating payment request to Intasend: Phone={phone}, Amount={amount}, Description={description}")

    try:
        if simulate:
            response =simulate_status("[RANDOM ID5]",0)
        else:
            LOG.api_logger.debug("Starting remote InstaSend request for phone: %s, amount: %s", phone, amount)

            service =initiate_intasend_service()

            response = service.collect.mpesa_stk_push(phone_number=phone, amount=amount, narrative=description)

            LOG.api_logger.debug(f"Received response from Intasend:Invoice id= {response['invoice']['invoice_id']}")

            if "errors" in response:
                raise


        session['response'] = response
        invoiceid = response['invoice']['invoice_id']


        add_payment_request(phone=phone , amount=amount ,order_id=orderid , invoice_id=invoiceid )

        return {"invoice_id": invoiceid, "status": response['invoice']['state']}
    except Exception as e:
        LOG.api_logger.error("An error occurred: %s", str(e))
        return None


USERNAME = "admin"
PASSWORD = "secure123"

@app.route("/" , methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        verified = UserManger.verify_user(email=email , password=password)
        if verified:
            session["logged_in"] = True
            return redirect("/dashboard")
        
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect("/login")
        return view_func(*args, **kwargs)
    return wrapper




@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")  


@app.route("/check-status" ,methods = ["POST"])
@token_required()
@content_type_is_json
@api_error_logger(logger = LOG.api_logger , in_development=IN_DEVELOPMENT)
def check_payment_status():
    
    data = request.get_json()
    
    SIMULATE  =data.get("SIMULATE", True)
    MAXRETRIES  = data.get("MAXRETRIES" , None)
    invoice_id = data.get("invoice_id", None)

    if not invoice_id:
        return jsonify({"MESSAGE": 'INVALID DATA'}), 404

    if not MAXRETRIES:
        MAXRETRIES = 3

    try:  
        service =initiate_intasend_service()

        for t in range(MAXRETRIES):
            LOG.api_logger.info(f"Checking payment status for InvoiceID={invoice_id}, Attempt={t+1}/{MAXRETRIES}")

            if SIMULATE:
                LOG.api_logger.info(f"Simulating payment status check for InvoiceID={invoice_id}, Elapsed Time={t}")

            status = service.collect.status(invoice_id) if not SIMULATE else simulate_status(invoice_id=invoice_id,elapsed_time=t+1)

            STAGE = status['invoice']['state']
            reason = status['invoice']['failed_reason']

            LOG.api_logger.debug("Status check result < INVOICE ID {} :STAGE {} :REASON {} >".format(invoice_id ,STAGE , reason))

            if reason == "Request cancelled by user":
                LOG.api_logger.info(f"Request cancelled by user InvoiceID={invoice_id}")
        
                update_payment_status(invoice_id=invoice_id , status="FAILED")
                return jsonify({"MESSAGE": "FAILED" ,"status":status}), 200


            if STAGE == 'COMPLETE':
                LOG.api_logger.info(f"Payment completed: InvoiceID={invoice_id}, New Status={status}")

                update_payment_status(invoice_id=invoice_id , status="COMPLETE")
                return jsonify({"MESSAGE": "COMPLETE" ,"status":status}), 200

            if STAGE == 'FAILED':
                LOG.api_logger.info(f"Payment failed: InvoiceID={invoice_id}")

                update_payment_status(invoice_id=invoice_id , status='FAILED')
                return jsonify ({"MESSAGE": "FAILED","status":status}), 400

            elif  STAGE == 'CANCELED':
                LOG.api_logger.info(f"Request cancelled by user: InvoiceID={invoice_id}")

                update_payment_status(invoice_id=invoice_id , status='FAILED')
                return jsonify( {"MESSAGE": "FAILED","status":status}), 400

            time.sleep(0.5)

        LOG.api_logger.info(f"Transaction was never  successfully completed :reason <{reason}> :invoice_id<{invoice_id}>")
        return jsonify({"MESSAGE": "WAITING","status":status}), 202

    except Exception as e:
        LOG.api_logger.error(f"Error occurred during payment processing: {str(e)}")
        LOG.api_logger.info("##"*35)
        return jsonify({"MESSAGE": "ERROR", 'error': str(e)}), 500



@app.route("/pay", methods=['POST'])
@token_required()
@content_type_is_json
@api_error_logger(logger = LOG.api_logger , in_development=IN_DEVELOPMENT)
def get_payment():

    data = request.get_json()
    phone = data.get("phone", None)
    price = data.get("amount", None)
    orderid = data.get('orderid' ,None)
        
    if price and phone and orderid :
       
        invoiceid = make_request_to_instasend(pub=PUBLISHABLE_KEY, key=SECRET_KEY, 
                                              phone=int(phone), 
                                              amount=int(float(price)) ,
                                              orderid = orderid,
                                               simulate = SIMULATE_TRANSFERS)
        if not invoiceid:
            return jsonify({"MESSAGE": 'INVALID DATA'}), 404
        else:
            return jsonify({"MESSAGE": "SUCCESS" , "response":invoiceid}) , 200
    else:
        return jsonify({"MESSAGE": 'INVALID DATA'}), 404


@app.route("/status/<invoice_id>", methods=['GET'])
@token_required()
@api_error_logger(logger = LOG.api_logger , in_development=IN_DEVELOPMENT)
def handle_payment_status_check(invoice_id):

    LOG.api_logger.info("[STATUS CHECK] invoice id: {} headers: {}".format(invoice_id,request.headers))

    payment_request =get_payment_status(invoice_id=invoice_id)

    if payment_request:
        return jsonify({"status": payment_request}), 200
    else:
        return jsonify({"MESSAGE": 'PAYMENT REQUEST NOT FOUND'}), 404
    
    
