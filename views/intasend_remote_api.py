from flask import Flask, request, jsonify, session 
from intasend import APIService
from dotenv import load_dotenv
import os

import logging


import time
from functools import wraps
from flask_cors import CORS

from utils.intasend_api_simulate import simulate_status
from db_manager.intasend_remote_db import update_payment_status , add_payment_request , get_payment_status



from views.transfer_api import transfer_bp ,token_required ,content_type_is_json
from utils.logger import LOG , api_error_logger
from models.transfers import create_db
from pathlib import Path

load_dotenv()
create_db()

app = Flask(__name__ ,
            static_folder=(Path(".")/'static').absolute())
CORS(app)

app.secret_key= os.getenv('FLASK_SECRET_KEY')
app.config['EXECUTOR_TYPE'] = 'threads'
app.config['EXECUTOR_PROPAGATE_EXCEPTIONS'] = True

app.register_blueprint(transfer_bp)


test = True
if not  os.getenv('SIMULATE_TRANSFERS','false').lower() == 'true':
    test= False

    PUBLISHABLE_KEY = os.getenv("PUB_KEY")
    SECRET_KEY = os.getenv("SECRET_KEY")

else:
    PUBLISHABLE_KEY = os.getenv("SANDBOX_PUBLISHABLE_KEY")
    SECRET_KEY = os.getenv("SANDBOX_SECRET_KEY")

API_TOKEN = os.getenv("API_TOKEN")
IN_DEVELOPMENT = os.getenv("IN_DEVELOPMENT", "false").lower() == 'true'
SIMULATE_TRANSFERS = os.getenv("SIMULATE_TRANSFERS", "true").lower() == 'true'

print(SIMULATE_TRANSFERS , IN_DEVELOPMENT)


def make_request_to_instasend(pub, key, phone: int, amount,orderid ,description="Purchase" , simulate=False):
    LOG.api_logger.info("__"*50)
    LOG.api_logger.info(f"Initiating payment request to Intasend: Phone={phone}, Amount={amount}, Description={description}")

    try:
        if simulate:
            response =simulate_status("[RANDOM ID5]",0)
        else:
            LOG.api_logger.debug("Starting remote InstaSend request for phone: %s, amount: %s", phone, amount)

            service = APIService(token=key, publishable_key=pub)
            response = service.collect.mpesa_stk_push(phone_number=phone, amount=amount, narrative=description)

            LOG.api_logger.debug(f"Received response from Intasend: {response}")

        session['response'] = response
        invoiceid = response['invoice']['invoice_id']


        add_payment_request(phone=phone , amount=amount ,order_id=orderid , invoice_id=invoiceid )

        return {"invoice_id": invoiceid, "status": response['invoice']['state']}
    except Exception as e:
        LOG.api_logger.error("An error occurred: %s", str(e))
        return None


@app.route("/check-status")
@token_required()
@content_type_is_json
@api_error_logger(logger = LOG.api_logger , in_development=IN_DEVELOPMENT)
def check_payment_status():
    
    LOG.api_logger.debug("##"*35)

    data = request.get_json()
    
    SIMULATE  =data.get("SIMULATE", True)
    MAXRETRIES  = data.get("MAXRETRIES" , None)
    invoice_id = data.get("invoice_id", None)
    if not invoice_id:
        return jsonify({"MESSAGE": 'INVALID DATA'}), 404
    

    if not MAXRETRIES:
        MAXRETRIES = 3

    try:  
        service = APIService(token=SECRET_KEY, publishable_key=PUBLISHABLE_KEY)

        for t in range(MAXRETRIES):
            LOG.api_logger.info(f"Checking payment status for InvoiceID={invoice_id}, Attempt={t+1}/{MAXRETRIES}")

            if SIMULATE:
                LOG.api_logger.info(f"Simulating payment status check for InvoiceID={invoice_id}, Elapsed Time={t}")
            status = service.collect.status(invoice_id) if not SIMULATE else simulate_status(invoice_id=invoice_id,elapsed_time=t+1)


            STAGE = status['invoice']['state']
            reason = status['invoice']['failed_reason']

            if reason == "Request cancelled by user":
                LOG.api_logger.info(f"Request cancelled by user InvoiceID={invoice_id}, New Status={status}")
                update_payment_status(invoice_id=invoice_id , status="FAILED")
                return jsonify({"MESSAGE": "FAILED" ,"status":status}), 200


            if STAGE == 'COMPLETE':
                LOG.api_logger.info(f"Payment status updated: InvoiceID={invoice_id}, New Status={status}")
                update_payment_status(invoice_id=invoice_id , status="COMPLETE")
                return jsonify({"MESSAGE": "COMPLETE" ,"status":status}), 200

            if STAGE == 'FAILED':
                LOG.api_logger.info(f"Payment status updated: InvoiceID={invoice_id}, New Status={status}")
                update_payment_status(invoice_id=invoice_id , status='FAILED')
                return jsonify ({"MESSAGE": "FAILED","status":status}), 400

            elif  STAGE == 'CANCELED':
                LOG.api_logger.info(f"Payment status updated: InvoiceID={invoice_id}, New Status={status}")
                update_payment_status(invoice_id=invoice_id , status='FAILED')
                return jsonify( {"MESSAGE": "FAILED","status":status}), 400

            time.sleep(0.5)

        LOG.api_logger.info(f"Transaction was never  successfully completed :reason <{reason}> :invoice_id<{invoice_id}>")
        LOG.api_logger.info("##"*35)
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
    """
    Initiate payment request to Intasend
    ---
    parameters:
      - name: phone
        in: body
        type: string
        required: true
        description: Phone number to send payment request to
      - name: amount
        in: body
        type: float
        required: true
        description: Amount to be paid
      - name: orderid
        in: body
        type: string
        required: true
        description: Order ID for the payment request
    responses:
      200:
        description: Payment request initiated successfully
      404:
        description: Invalid data provided
    
    """
    data = request.get_json()
    phone = data.get("phone", None)
    price = data.get("amount", None)
    orderid = data.get('orderid' ,None)
    
    session.update(data)
 
    
    if price and phone and orderid :
        LOG.api_logger.debug(f"FIRST REQUEST making remote pay requests to {phone}")
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
    
    