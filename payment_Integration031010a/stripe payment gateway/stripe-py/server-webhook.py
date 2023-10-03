
import stripe
import json
from flask import Flask, jsonify, request

app = Flask(__name__)

# YOUR_DOMAIN = 'http://localhost:5000'

stripe.api_key = "sk_test_51NmV6MSEBetulxsVicdnvKuYGaagPuOQXLYqVYHEYw2MzFYRcjFjAFFoE7yIufHmCpe6Gu5UacQCSqh2byerWqyG00z8vOJ3Cq"
                # sk_test_51NmV6MSEBetulxsVicdnvKuYGaagPuOQXLYqVYHEYw2MzFYRcjFjAFFoE7yIufHmCpe6Gu5UacQCSqh2byerWqyG00z8vOJ3Cq


@app.route('/webhook', methods=['POST'])
def webhook():
    json_payload = json.loads(request.data)
    event = stripe.Event.construct_from(
        json_payload, stripe.api_key
    )
    print(event.type)
    print(type(event.data.object))
    print(event.data.object.id)
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True, port=4242)
