from flask import Flask, request, jsonify
import stripe

app = Flask(__name__)

stripe.api_key = "sk_test_51NmV6MSEBetulxsVicdnvKuYGaagPuOQXLYqVYHEYw2MzFYRcjFjAFFoE7yIufHmCpe6Gu5UacQCSqh2byerWqyG00z8vOJ3Cq"


@app.route('/pay', methods=['POST'])
def create_payment_intent():
    # Get the customer's payment details
    email = request.args.get('email')

    # Create a new payment intent
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=50100,
            currency='usd',
            email=email,
            
            payment_method_types=['card'],
            setup_future_usage='off_session'
        )
        return jsonify({'payment_intent': payment_intent}), 201
    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to create payment intent'}), 400




@app.route('/webhook', methods=['POST'])
def webhook():
    # Get the incoming webhook data from Stripe
    data = request.get_json()

    # Check if the webhook is valid
    sig = data.pop('stripe_signature')
    event = data.pop('event')
    if not stripe.Webhook.validate_request(req, event):
        return jsonify({'error': 'Invalid webhook signature'}), 400

    # Process the webhook event
    if event['type'] == 'payment_intent.created':
        # Handle payment intent creation
        payment_intent_id = event['data']['object']['id']
        # customer_id = event['data']['object']['customer']
        amount = event['data']['object']['amount']
        currency = event['data']['object']['currency']
        print(f"Payment intent created: {payment_intent_id}, Amount: {amount}, Currency: {currency}")
    elif event['type'] == 'payment_intent.succeeded':
        # Handle payment success
        payment_intent_id = event['data']['object']['id']
        # customer_id = event['data']['object']['customer']
        amount = event['data']['object']['amount']
        currency = event['data']['object']['currency']
        print(f"Payment succeeded: {payment_intent_id}, Amount: {amount}, Currency: {currency}")
    else:
        print("Unhandled webhook event type")

    return jsonify({'message': 'Webhook received'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5333)

