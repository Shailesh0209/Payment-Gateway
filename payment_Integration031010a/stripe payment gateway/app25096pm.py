from flask import Flask, request
from flask_cors import CORS
import stripe
import json
# import pymysql

# stripe.api_key = 'sk_test_....'

# endpoint_secret = 'whsec_...'

app = Flask(__name__)
CORS(app)


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



user_info = {}

@app.route('/pay', methods=['POST'])
def pay():
    email = request.args.get('email', None)

    if not email:
        return 'You need to send an Email!', 400

    intent = stripe.PaymentIntent.create(
        amount=50100,
        currency='usd',
        # automatic_payment_methods={"enabled": True},
        payment_method_types=['card'],
        setup_future_usage='off_session',
        # payment_method='pm_1234567890',

        receipt_email=email
    )

    return {"client_secret": intent['client_secret']}, 200

@app.route('/paymentWebhook', methods=['POST'])
def webhook():
    payload = request.get_data()
    sig_header = request.headers.get('Stripe_Signature', None)

    if not sig_header:
        return 'No Signature Header!', 400

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header
        )
    except ValueError as e:
        # Invalid payload
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return 'Invalid signature', 400

    if event['type'] == 'payment_intent.succeeded':
        email = event['data']['object']['receipt_email'] # contains the email that will recive the recipt for the payment (users email usually)
        
        user_info['paid_50'] = True
        user_info['email'] = email
    else:
        return 'Unexpected event type', 400

    return '', 200

@app.route('/user', methods=['GET'])
def user():
    return user_info, 200

if __name__ == '__main__':
    app.run(debug=True, port=5333)