import pandas as pd
import random

random.seed(42)

customers = [
    "Rahul", "Priya", "Aman", "Neha", "Riya",
    "Arjun", "Karan", "Sneha", "Vikram", "Ananya"
]

orders = []
payments = []

# Create 100 orders
for i in range(1, 101):

    order_id = f"ORD{i:03d}"

    amount = random.choice([
        500, 750, 1000, 1200,
        1500, 2000, 2500, 3000, 5000
    ])

    customer = random.choice(customers)

    orders.append({
        "order_id": order_id,
        "customer": customer,
        "order_amount": amount
    })

    # Normally payment = order amount
    payment_amount = amount

    # Amount mismatch
    if i % 10 == 0:
        payment_amount = amount - 200

    # Missing payment
    elif i % 15 == 0:
        continue

    payments.append({
        "payment_id": f"PAY{i:03d}",
        "order_id": order_id,
        "payment_amount": payment_amount,
        "status": "SUCCESS"
    })


# Add duplicate payment
payments.append({
    "payment_id": "PAY_DUP_001",
    "order_id": "ORD005",
    "payment_amount": 1000,
    "status": "SUCCESS"
})

# Add unknown payment
payments.append({
    "payment_id": "PAY_UNKNOWN_001",
    "order_id": "ORD999",
    "payment_amount": 1500,
    "status": "SUCCESS"
})


# Convert to DataFrames
orders_df = pd.DataFrame(orders)
payments_df = pd.DataFrame(payments)


# Save CSV files
orders_df.to_csv("orders.csv", index=False)
payments_df.to_csv("payments.csv", index=False)


print("================================")
print("FINANCE DATA CREATED")
print("================================")
print(f"Orders created: {len(orders_df)}")
print(f"Payments created: {len(payments_df)}")
print("orders.csv created")
print("payments.csv created")