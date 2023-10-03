from flask import Flask, request, jsonify
import stripe
import json
import pymysql

# logging file
import logging
import datetime


# Configure the logger for responses
response_logger = logging.getLogger('response_logger')
response_logger.setLevel(logging.INFO)
response_formatter = logging.Formatter('%(asctime)s - %(message)s')
now = datetime.datetime.now()            
timestamp = now.strftime("_%Y-%m-%d")
log_file = "log_file" + timestamp + ".log"
# logging.basicConfig(filename = log_file,format = '%(asctime)s %(message)s',filemode = 'a')

logging.basicConfig(filename=log_file, format='%(asctime)s - %(levelname)s - %(message)s', filemode='a')
root_logger = logging.getLogger()
root_logger.setLevel(logging.ERROR)  
root_logger.setLevel(logging.INFO)


app = Flask(__name__)


# Configure your MySQL database settings
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'aizendb'

# Create a PyMySQL connection to the database
connection = pymysql.connect(
    host=app.config['MYSQL_HOST'],
    user=app.config['MYSQL_USER'],
    password=app.config['MYSQL_PASSWORD'],
    db=app.config['MYSQL_DB']
)


# Set your Stripe API keys
# stripe.api_key = "YOUR_STRIPE_SECRET_KEY"
stripe.api_key = "sk_test_51NmV6MSEBetulxsVicdnvKuYGaagPuOQXLYqVYHEYw2MzFYRcjFjAFFoE7yIufHmCpe6Gu5UacQCSqh2byerWqyG00z8vOJ3Cq"


@app.route('/getAllCustomers', methods=['GET'])
def get_customers():
    try:
        customers = stripe.Customer.list(limit=100)  # You can adjust the limit as needed

        # Extract customer data and convert it to a list
        customer_list = [{"id": customer.id, "name": customer.name, "email": customer.email} for customer in customers]

        return jsonify({"customers": customer_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/createOnlinePayment', methods=['POST'])
def create_online_payment():
    try:
        amount = request.args.get('amount', type=float)
        order_receipt = request.args.get('user_id', type=str)

        if not amount or not order_receipt:
            response_logger.info("createOnlinePayment: order_receipt: %s error: Mandatory field is missing", order_receipt, exc_info=True)
            return jsonify({"Message": "Mandatory field is missing", "result_code": 1})

        # Convert payment_method_types set to a list
        payment_method_types = ['card']

        # Create a payment intent with Stripe
        payment_intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Amount in cents
            currency='INR',  # Change to your desired currency
            receipt_email=order_receipt,
            payment_method_types=payment_method_types,  # Use the list here
            metadata={
                'user_id': order_receipt
            }
        )

        payment_intent = stripe.PaymentIntent.confirm(
            payment_intent.id,
            payment_method='pm_card_visa',
            use_stripe_sdk=True,
            payment_method_options={
                'card': {
                    'request_three_d_secure': 'any',
                }
            }
        )

        payment_id = payment_intent.id
        status = payment_intent.status

        if status == 'requires_payment_method':
            response_logger.info("createOnlinePayment: order_receipt: %s : message: Payment ID is not created", order_receipt, exc_info=True)
            return jsonify({"Message": "Payment ID is not created. Please provide a valid payment method.", "result_code": 1})

        # Update your database with the payment details
        # Replace this with your database code
        response_logger.info("createOnlinePayment: order_receipt: %s : message: Successfully created online payment id", order_receipt, exc_info=True)
        return jsonify({"Message": "Successfully created online payment id", "result_code": 0}), 200

    except Exception as e:
        response_logger.info("createOnlinePayment: order_receipt: %s : message: An error occurred while inserting details in DB : error: %s", order_receipt, str(e), exc_info=True)
        return jsonify({"Message": f"An error occurred while inserting details in DB", "error": str(e), "result_code": 1}), 200



@app.route('/paymentWebhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    event = None

    try:
        event = stripe.Event.construct_from(
            json.loads(payload), stripe.api_key
        )

        if event.type == 'checkout.session.completed':
            # Handle the checkout.session.completed event here
            # You can access event.data.object for details

            # Example: Log payment details to your database
            payment_intent_id = event.data.object.payment_intent
            amount = event.data.object.amount_total / 100
            userid = event.data.object.customer_details.email
            order_success_id = event.data.object.id
            payment_status = "paid"

            # Insert this data into your database
            with connection.cursor() as cursor:
                updQuery = "INSERT INTO `GENVERSE_PAYMENT` (`Payment_Id`, `User_Id`, `Amount`, `Order_Success_id`, `Payment_Status`) VALUES (%s,%s,%s,%s, %s)"
                cursor.execute(updQuery,(payment_intent_id, userid, amount, order_success_id, payment_status),)
                connection.commit()
                cursor.close()

    except Exception as e:
        # Handle any exceptions that occur during webhook processing
        return str(e), 400

    return jsonify({'payment_intent_id': payment_intent_id, 'amount': amount, 'userid': userid, 'order_success_id': order_success_id, 'payment_status': payment_status}), 200 







if __name__ == '__main__':
    app.run(debug=True, port=5333)



# @app.route('/createOnlinePayment', methods=['POST'])
# def create_online_payment():
#     try:
#         amount = request.args.get('amount', type=float)
#         order_receipt = request.args.get('user_id', type=str)

#         if not amount or not order_receipt:
#             response_logger.info("createOnlinePayment: order_receipt: %s error: Mandatory field is missing", order_receipt, exc_info=True)
#             return jsonify({"Message": "Mandatory field is missing", "result_code": 1})

#         # Convert payment_method_types set to a list
#         payment_method_types = ['card']

#         # Create a payment intent with Stripe
#         payment_intent = stripe.PaymentIntent.create(
#             amount=int(amount * 100),  # Amount in cents
#             currency='INR',  # Change to your desired currency
#             receipt_email=order_receipt,
#             payment_method_types=payment_method_types,  # Use the list here
            
            
#             payment_method_options={
#                 'request_three_d_secure': 'any',
#             },
#             metadata={
#                 'user_id': order_receipt
#             }
#         )
#         payment_intent = stripe.PaymentIntent.confirm(
#             payment_intent.id,
#             payment_method='pm_card_visa',
#             use_stripe_sdk=True,
#         )

#         payment_id = payment_intent.id
#         status = payment_intent.status

#         if status == 'requires_payment_method':
#             response_logger.info("createOnlinePayment: order_receipt: %s : message: Payment ID is not created", order_receipt, exc_info=True)
#             return jsonify({"Message": "Payment ID is not created. Please provide a valid payment method.", "result_code": 1})

#         # Update your database with the payment details
#         # Replace this with your database code
#         response_logger.info("createOnlinePayment: order_receipt: %s : message: Successfully created online payment id", order_receipt, exc_info=True)
#         return jsonify({"Message": "Successfully created online payment id", "result_code": 0}), 200

#     except Exception as e:
#         response_logger.info("createOnlinePayment: order_receipt: %s : message: An error occurred while inserting details in DB : error: %s", order_receipt, str(e), exc_info=True)
#         return jsonify({"Message": f"An error occurred while inserting details in DB", "error": str(e), "result_code": 1}), 200



# @app.route('/createOnlinePayment', methods=['POST'])
# def create_online_payment():
#     try:
#         amount = request.args.get('amount', type=float)
#         order_receipt = request.args.get('user_id', type=str)

#         if not amount or not order_receipt:
#             response_logger.info("createOnlinePayment: order_receipt: %s error: Mandatory field is missing", {order_receipt}, exc_info=True)
#             return jsonify({"Message": "Mandatory field is missing", "result_code": 1})

#         # Create a payment intent with Stripe
#         payment_intent = stripe.PaymentIntent.create(
#             amount=int(amount * 100),  # Amount in cents
#             currency='INR',  # Change to your desired currency
#             receipt_email=order_receipt,
#             payment_method_types=['card'],
#             payment_method_data={
#                 "type": "card",
#                 "card": {
#                     "number": "4242424242424242",
#                     "exp_month": 12,
#                     "exp_year": 2024,
#                     "cvc": "314"
#                 }
#             },

            
#             metadata={
#                 'user_id': order_receipt
#             }
#         )
#         payment_intent = stripe.PaymentIntent.confirm(
#             payment_intent.id,
#             payment_method='pm_card_visa',
#             use_stripe_sdk=True,
#         )


#         payment_id = payment_intent.id
#         status = payment_intent.status

#         if status == 'requires_payment_method':
#             response_logger.info("createOnlinePayment: order_receipt: %s : message: Payment ID is not created", {order_receipt}, exc_info=True)
#             return jsonify({"Message": "Payment ID is not created. Please provide a valid payment method.", "result_code": 1})

#         # Update your database with the payment details
#         # Replace this with your database code
#         response_logger.info("createOnlinePayment: order_receipt: %s : message: Successfully created online payment id", {order_receipt}, exc_info=True)
#         return jsonify({"Message": "Successfully created online payment id", "result_code": 0}), 200

#     except Exception as e:
#         response_logger.info("createOnlinePayment: order_receipt: %s : message: An error occurred while inserting details in DB : error: %s", {order_receipt, str(e)}, exc_info=True)
#         return jsonify({"Message": f"An error occurred while inserting details in DB", "error": {str(e)}, "result_code": 1}), 200



# # @app.route('/createOnlinePayment', methods=['POST'])
# # def create_online_payment():
#     try:
#         amount = request.args.get('amount', type=float)
#         order_receipt = request.args.get('user_id', type=str)

#         if not amount or not order_receipt:
#             response_logger.info("createOnlinePayment : order_receipt: %s error : Mandatory field is missing",{order_receipt}, exc_info=True)
#             return jsonify({ "Message":"Mandatory field is missing","result_code":1})
#             # return jsonify({"Message": "Mandatory field is missing", "result_code": 1})

#         # Create a payment intent with Stripe
#         payment_intent = stripe.PaymentIntent.create(
#             amount=int(amount * 100),  # Amount in cents
#             currency='INR',            # Change to your desired currency
#             receipt_email=order_receipt,
#             metadata={
#                 'user_id': order_receipt
#             }

#         )

#         payment_id = payment_intent.id
#         status = payment_intent.status

#         if status == 'requires_payment_method':
#             response_logger.info("createOnlinePayment : order_receipt: %s : message : Payment ID is not created",{order_receipt},  exc_info=True)
#             return jsonify({"Message": "Payment ID is not created", "result_code": 1})
#             # return jsonify({"Message": "Payment ID is not created", "result_code": 1})

#         # Update your database with the payment details
#         # Replace this with your database code
#         response_logger.info("createOnlinePayment : order_receipt: %s : message : Successfully created online payment id",{order_receipt}, exc_info=True)
#         return jsonify({"Message": "Successfully created online payment id", "result_code": 0}), 200

#     except Exception as e:
#         response_logger.info("createOnlinePayment : order_receipt: %s : message : An error occurred while inserting details in DB : error : %s",{order_receipt,str(e)},  exc_info=True)
#         return jsonify({"Message": f"An error occurred while inserting details in DB"," error": {str(e)}, "result_code": 1}), 200
#         # return jsonify({"Message": str(e), "result_code": 1}), 500



# @app.route('/paymentWebhook', methods=['POST'])
# def webhook():
#     payload = request.get_data()
#     sig_header = request.headers.get('Stripe_Signature', None)

#     if not sig_header:
#         return 'No Signature Header!', 400

#     try:
#         event = stripe.Webhook.construct_event(
#             payload, sig_header
#         )
#     except ValueError as e:
#         # Invalid payload
#         return 'Invalid payload', 400
#     except stripe.error.SignatureVerificationError as e:
#         # Invalid signature
#         return 'Invalid signature', 400

#     if event['type'] == 'payment_intent.succeeded':
#         email = event['data']['object']['receipt_email'] # contains the email that will recive the recipt for the payment (users email usually)
        
#         user_info['paid_50'] = True
#         user_info['email'] = email
#     else:
#         return 'Unexpected event type', 400

#     return '', 200

# @app.route('/paymentWebhook', methods=['POST'])
# def payment_webhook():
#     try:
#         connection.begin()
#         payload = request.body
#         event = None
        
#         event = stripe.Event.construct_from(
#             json.loads(payload), stripe.api_key
#         )
#         print("event--------**-------",event)
#         print("111111111111111111111111111111111111111111111111111")

#         event_type = event.type  # Get the event type from the Stripe event


#         # Handle different types of Stripe events
#         if event_type == 'checkout.session.completed':  # Corrected event type
#             print("222222222222222222222222222222222222222222222")
#             checkout_session = event.data.object
#             payment_intent_id = checkout_session.payment_intent
#             amount = checkout_session.amount_total/100
#             userid = checkout_session.customer_details.email
#             order_success_id = checkout_session.id
#             payment_status = "paid"
#             print("444444444444444444444444444444444444444444444")
#             print(checkout_session, payment_intent_id, amount, userid, order_success_id, payment_status)
#             # Update your database based on the payment status
#             with connection.cursor() as cursor:
#                 updQuery = "INSERT INTO `GENVERSE_PAYMENT` (`Payment_Id`, `User_Id`, `Amount`, `Order_Success_id`, `Payment_Status`) VALUES (%s,%s,%s,%s, %s)"
#                 cursor.execute(updQuery,(payment_intent_id, userid, amount, order_success_id, payment_status),)
#                 connection.commit()
#                 cursor.close()
            
#             response_logger.info("paymentWebhook : payment_webhook : message : Payment details updated successfully", {"userid": userid}, exc_info=True)
#             return jsonify({"Message": "Payment details updated successfully", "result_code": 0})

#     except Exception as e:
#         return jsonify({"Message": str(e), "result_code": 1}), 500


# @app.route('/paymentWebhook', methods=['POST'])
# def payment_webhook():
#     try:
#         connection.begin()
#         payload = request.data.decode('utf-8')
#         event = stripe.Event.construct_from(
#             json.loads(payload), stripe.api_key
#         )

#         # Handle different types of Stripe events
#         if event.type == 'checkout.session.compeleted':
#             checkout_session = event.data.object
#             payment_intent_id = checkout_session.payment_intent
#             amount = checkout_session.amount_total/100
#             userid = checkout_session.customer_details.email
#             order_success_id = checkout_session.id
#             payment_status = "paid"

#             # Update your database based on the payment status
#             with connection.cursor() as cursor:
#                 updQuery = "Insert into `GENVERSE_PAYMENT` (`Payment_Id`, `User_Id`, `Amount`, `Order_Success_id`, `Payment_Status`) VALUES (%s,%s,%s,%s, %s)"
#                 cursor.execute(updQuery,(payment_intent_id,userid,amount, order_success_id, payment_status),)
#                 connection.commit()
#                 cursor.close()
#             # Replace this with your database code
#             # print("payment_intent.succeeded", payment_intent, payment_id, userid, order_success_id, payment_status)
#             response_logger.info("paymentWebhook : payment_webhook : message : Payment details updated successfully",{userid}, exc_info=True)
#             return jsonify({"Message": "Payment details updated successfully", "result_code": 0})

#     except Exception as e:
#         return jsonify({"Message": f"An error occurred: {str(e)}", "result_code": 1}), 500
