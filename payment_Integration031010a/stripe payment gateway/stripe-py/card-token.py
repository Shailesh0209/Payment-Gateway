import stripe
stripe.api_key = "sk_test_51NmV6MSEBetulxsVicdnvKuYGaagPuOQXLYqVYHEYw2MzFYRcjFjAFFoE7yIufHmCpe6Gu5UacQCSqh2byerWqyG00z8vOJ3Cq"

stripe.Token.create(
  card={
    "number": "4242424242424242",
    "exp_month": 9,
    "exp_year": 2024,
    "cvc": "314",
  },
)