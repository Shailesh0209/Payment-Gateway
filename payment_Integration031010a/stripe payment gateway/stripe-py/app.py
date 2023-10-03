from flask import Flask, redirect, request, jsonify
import stripe
import json
import os
import pymysql

app = Flask(__name__, static_url_path="", static_folder="public")

# Configure your MySQL database settings
app.config['MYSQL_HOST'] = '109.106.255.67'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Innoknights@19'
app.config['MYSQL_DB'] = 'aizendb'

# Configure your MySQL database settings
# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = ''
# app.config['MYSQL_DB'] = 'aizendb'

# Create a PyMySQL connection to the database
connection = pymysql.connect(
    host=app.config['MYSQL_HOST'],
    user=app.config['MYSQL_USER'],
    password=app.config['MYSQL_PASSWORD'],
    db=app.config['MYSQL_DB']
)


YOUR_DOMAIN = 'http://localhost:5333'

stripe.api_key = "sk_test_51NmV6MSEBetulxsVicdnvKuYGaagPuOQXLYqVYHEYw2MzFYRcjFjAFFoE7yIufHmCpe6Gu5UacQCSqh2byerWqyG00z8vOJ3Cq"
                

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/checkout', methods=['POST'])
def checkout():
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
            # {
            #     'price': 'price_1NmWVwSEBetulxsVCTAz3qjS',
            #     'quantity': 1,
            # },
            # {
            #     'price': 'price_1NmWboSEBetulxsVy4mJS7ai',
            #     'quantity': 1,
            # },
            {
                'price': 'price_1NmaRZSEBetulxsVp1ZEga9Y',
                'quantity': 1,
            },
            
            ],
            mode='payment',
            success_url=YOUR_DOMAIN + '/success.html',
            cancel_url=YOUR_DOMAIN + '/cancel.html',
        )            
    except Exception as e:
        return str(e)
    
    return redirect(checkout_session.url, code=303)

# Webhook endpoint to process payments for sources asynchronously.
endpoint_secret = 'whsec_8aa09bbd216f5175d3cc2698afe1a782897920fdcdc75c0c11dae07d922367cc'

@app.route('/webhook', methods=['POST'])
def webhook():
    event = None
    payload = request.data

    try:
        event = json.loads(payload)
    except json.decoder.JSONDecodeError as e:
        print('⚠️  Webhook error while parsing basic request.' + str(e))
        return jsonify(success=False)

    if endpoint_secret:
        sig_header = request.headers.get('stripe-signature')
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except stripe.error.SignatureVerificationError as e:
            print('⚠️  Webhook signature verification failed.' + str(e))
            return jsonify(success=False)

    # handle stripe checkouts that are successful
    if event['type'] == 'checkout.session.completed':
        # print("11111111111111111111111111111111111111111111111111")
        session = event['data']['object']
        # print("session*******************", session)
        payment_intent = stripe.PaymentIntent.retrieve(session['payment_intent'])
        payment_id = payment_intent['id']
        # print("payment Intent------------------------------------", payment_intent)
        amount = payment_intent['amount']
        email = session['customer_details']['email']
        # get userid from email from aizen user table
        userid = None
        with connection.cursor() as cursor:
            selQuery = "SELECT User_Id FROM `AIZEN_USER` WHERE `Email_Id` = %s"
            cursor.execute(selQuery,(email,))
            result = cursor.fetchone()
            # print("result------------------------------------", result)
            # cursor.close()
        # userid = result[0]

        # Check if a user with the given email exists in your database
        if result:
            userid = result[0]
            # print("userid------------------------------------", userid)
        else:
            userid = 1
            # Handle the case where the user with the email is not found in your database
            # print("User with email {} not found in the database".format(email))

        order_success_id = f"{event['data']['object']['id']}"
        payment_status = payment_intent['status']
        print('Payment for {} succeeded'.format(payment_intent['amount']))

        # Insert the order into the database
        with connection.cursor() as cursor:
            updQuery = "INSERT INTO `GENVERSE_PAYMENT` (`Payment_Id`, `User_Id`, `Amount`, `Order_Success_id`, `Payment_Status`) VALUES (%s,%s,%s,%s, %s)"
            cursor.execute(updQuery,(payment_id, userid, amount, order_success_id, payment_status),)
            connection.commit()
            cursor.close()

    else:
        # Unexpected event type
        print('Unhandled event type {}'.format(event['type']))

    return jsonify(success=True), 200



if __name__ == '__main__':
    app.run(debug=True, port=5333)






        
    #     # payment_intent = event['data']['object']  # contains a stripe.PaymentIntent
    #     # print('Payment for {} succeeded'.format(payment_intent['amount']))
    #     # Then define and call a method to handle the successful payment intent.
    #     # handle_payment_intent_succeeded(payment_intent)

    # elif event['type'] == 'payment_intent.requires_action':
    #     # This event type does not contain a 'payment_intent' field.
    #     # Handle it as needed.
    #     print("22222222222222222222222222222222222222222222222222222222222")
    #     print('Payment intent requires action')
    #     payment_intent = event['data']['object']
    #     amount = payment_intent['amount']
    #     # userid = payment_intent['metadata']['userid']
    #     userid = payment_intent['metadata']
    #     # order_success_id = payment_intent['metadata']['order_success_id']
    #     order_success_id = payment_intent['metadata']
    #     payment_status = payment_intent['status']
    #     print('Payment for {} succeeded'.format(payment_intent['amount']))

    #     # Insert the order into the database
    #     with connection.cursor() as cursor:
    #         updQuery = "INSERT INTO `GENVERSE_PAYMENT` (`Payment_Id`, `User_Id`, `Amount`, `Order_Success_id`, `Payment_Status`) VALUES (%s,%s,%s,%s, %s)"
    #         cursor.execute(updQuery,(payment_intent, userid, amount, order_success_id, payment_status),)
    #         connection.commit()
    #         cursor.close()

    # if event['type'] == 'payment_intent.created':
    #     # This event type also does not contain a 'payment_intent' field.
    #     # Handle it as needed.
    #     print("3333333333333333333333333333333333333333333333333333333333")
    #     print('Payment intent created')
    #     payment_intent = event['data']['object']
    #     payment_id = payment_intent['id']
    #     amount = payment_intent['amount']
    #     # userid = payment_intent['metadata']['userid']
    #     userid = payment_intent['metadata']
    #     # order_success_id = payment_intent['metadata']['order_success_id']
    #     order_success_id = payment_intent['metadata']
    #     payment_status = payment_intent['status']
    #     print('Payment for {} succeeded'.format(payment_intent['amount']))

    #     # Insert the order into the database
    #     with connection.cursor() as cursor:
    #         updQuery = "INSERT INTO `GENVERSE_PAYMENT` (`Payment_Id`, `User_Id`, `Amount`, `Order_Success_id`, `Payment_Status`) VALUES (%s,%s,%s,%s, %s)"
    #         cursor.execute(updQuery,(payment_id, userid, amount, order_success_id, payment_status),)
    #         connection.commit()
    #         cursor.close()

    # if event['type'] == 'payment_intent.succeeded':
    #     # This event type contains a 'payment_intent' field.
    #     print("4444444444444444444444444444444444444444444444444444444")
    #     payment_intent = event['data']['object']
    #     payment_id = payment_intent['id']
    #     amount = payment_intent['amount']
    #     userid = payment_intent['metadata']
    #     order_success_id = payment_intent['metadata']['order_success_id']
    #     payment_status = payment_intent['status']
    #     print('Payment for {} succeeded'.format(payment_intent['amount']))

    #     # Insert the order into the database
    #     with connection.cursor() as cursor:
    #         updQuery = "INSERT INTO `GENVERSE_PAYMENT` (`Payment_Id`, `User_Id`, `Amount`, `Order_Success_id`, `Payment_Status`) VALUES (%s,%s,%s,%s, %s)"
    #         cursor.execute(updQuery,(payment_id, userid, amount, order_success_id, payment_status),)
    #         connection.commit()
    #         cursor.close()




# @app.route('/webhook', methods=['POST'])
# def webhook():
#     event = None
#     payload = request.data
#     # payload = request.get_data(as_text=True)

#     try:
#         event = json.loads(payload)
#     except json.decoder.JSONDecodeError as e:
#         print('⚠️  Webhook error while parsing basic request.' + str(e))
#         return jsonify(success=False)
#     if endpoint_secret:
#         # Only verify the event if there is an endpoint secret defined
#         # Otherwise use the basic event deserialized with json
#         sig_header = request.headers.get('stripe-signature')
#         # sig_header = request.headers['stripe-signature']
#         try:
#             event = stripe.Webhook.construct_event(
#                 payload, sig_header, endpoint_secret
#             )
#         except stripe.error.SignatureVerificationError as e:
#             print('⚠️  Webhook signature verification failed.' + str(e))
#             return jsonify(success=False)

#     # Handle the event for stripe checkouts

#     # if event['type'] == 'checkout.session.completed':
#     # event requires action

#     if event['type'] == 'payment_intent.requires_action':
#         session = event['data']['object']
#         payment_intent = stripe.PaymentIntent.retrieve(session['payment_intent'])
#         amount = payment_intent['amount']
#         userid = payment_intent['metadata']['userid']
#         order_success_id = payment_intent['metadata']['order_success_id']
#         payment_status = payment_intent['status']
#         print('Payment for {} succeeded'.format(payment_intent['amount']))

#         # Insert the order into the database
#         with connection.cursor() as cursor:
#             updQuery = "INSERT INTO `GENVERSE_PAYMENT` (`Payment_Id`, `User_Id`, `Amount`, `Order_Success_id`, `Payment_Status`) VALUES (%s,%s,%s,%s, %s)"
#             cursor.execute(updQuery,(payment_intent, userid, amount, order_success_id, payment_status),)
#             connection.commit()
#             cursor.close()
        
#         # payment_intent = event['data']['object']  # contains a stripe.PaymentIntent
#         # print('Payment for {} succeeded'.format(payment_intent['amount']))
#         # Then define and call a method to handle the successful payment intent.
#         # handle_payment_intent_succeeded(payment_intent)
#     elif event['type'] == 'payment_intent.created':
#         payment_method = event['data']['object']  # contains a stripe.PaymentMethod
#         print('Payment for {} succeeded'.format(payment_method['amount']))

#         # Then define and call a method to handle the successful attachment of a PaymentMethod.
#         # handle_payment_method_attached(payment_method)
#     else:
#         # Unexpected event type
#         print('Unhandled event type {}'.format(event['type']))

#     return jsonify(success=True), 200

# @app.route('/webhook', methods=['POST'])
# def webhook():
#     payload = request.data
#     sig_header = request.headers.get('stripe-signature')

#     try:
#         event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
#         print("event", event)
#         # insert into genverse_payment table
#         # Insert the order into the database

#     except stripe.error.SignatureVerificationError as e:
#         print('Webhook signature verification failed: ' + str(e))
#         return jsonify(success=False)

#     # Handle the event here

#     return jsonify(success=True), 200



# import stripe
# customer = stripe.Customer.retrieve(
#   "cus_OZfD7IbDw0GlgS",
#   api_key="sk_test_51NmV6MSEBetulxsVicdnvKuYGaagPuOQXLYqVYHEYw2MzFYRcjFjAFFoE7yIufHmCpe6Gu5UacQCSqh2byerWqyG00z8vOJ3Cq"
# )
# customer.capture() # Uses the same API Key.