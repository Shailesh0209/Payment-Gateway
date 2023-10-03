import stripe

def process_payment(amount):
  """Processes a payment of the specified amount."""

  # Create a Stripe charge object.
  charge = stripe.Charge.create(
    amount=10,
    currency="usd",
  )

  # Check if the charge was successful.
  if charge.status == "paid":
    return True
  else:
    return False
