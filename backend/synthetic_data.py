import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
import random
import pandas as pd
from datetime import datetime, timedelta

def generate_synthetic_finance_data(num_records: int = 150, seed: int = 42):
    random.seed(seed)
    
    customers = [
        "Rahul Sharma", "Priya Nair", "Aman Gupta", "Neha Patel", "Vikram Mehta",
        "Sneha Reddy", "Karan Verma", "Ananya Iyer", "Rohan Kapoor", "Pooja Deshmukh",
        "Aditya Joshi", "Kavita Rao", "Siddharth Jain", "Meera Sen", "Harsh Vardhan",
        "Tanvi Kulkarni", "Deepak Chawla", "Shreya Bhat", "Manish Tiwari", "Divya Menon"
    ]
    
    payment_methods = ["UPI", "Credit Card", "Debit Card", "Netbanking"]
    method_weights = [0.45, 0.25, 0.15, 0.15]
    
    amounts_pool = [
        499, 750, 999, 1250, 1500, 1999, 2450, 3200, 
        4500, 5999, 7500, 9800, 12500, 16000, 22000
    ]
    
    now = datetime.now()
    orders = []
    payments = []
    settlements = []
    
    base_order_count = num_records
    
    # We will plan anomaly counts based on total records
    # e.g., for 150 records: ~10 missing, ~8 amount mismatch, ~4 duplicate, ~5 unknown, ~6 settlement mismatch
    missing_indices = set(range(12, base_order_count, 14))
    mismatch_indices = set(range(7, base_order_count, 15))
    duplicate_indices = set(range(18, base_order_count, 28))
    settle_mismatch_indices = set(range(9, base_order_count, 20))
    
    # Avoid overlapping indices for clean demonstrations
    missing_indices = missing_indices - mismatch_indices - duplicate_indices - settle_mismatch_indices
    mismatch_indices = mismatch_indices - duplicate_indices - settle_mismatch_indices
    
    for i in range(1, base_order_count + 1):
        order_id = f"ORD_{i:04d}"
        customer = random.choice(customers)
        amount = float(random.choice(amounts_pool))
        days_ago = random.uniform(1, 28)
        created_at = (now - timedelta(days=days_ago, hours=random.uniform(0, 12))).strftime("%Y-%m-%d %H:%M:%S")
        method = random.choices(payment_methods, weights=method_weights)[0]
        
        orders.append({
            "order_id": order_id,
            "customer": customer,
            "order_amount": amount,
            "payment_method": method,
            "created_at": created_at
        })
        
        # 1. MISSING PAYMENT: Skip payment creation
        if i in missing_indices:
            continue
            
        # 2. AMOUNT MISMATCH: Payment amount differs from order amount
        if i in mismatch_indices:
            diff_type = random.choice([-1, 1])
            mismatch_delta = random.choice([200.0, 350.0, 500.0, 1000.0])
            payment_amount = max(100.0, amount + (diff_type * mismatch_delta))
        else:
            payment_amount = amount
            
        pay_id = f"pay_rzp_{i:04d}x{random.randint(10, 99)}"
        fee_rate = 0.0236 if method in ["Credit Card", "Netbanking"] else 0.005 # 2.36% or 0.5%
        gateway_fee = round(payment_amount * fee_rate, 2)
        
        payments.append({
            "payment_id": pay_id,
            "order_id": order_id,
            "payment_amount": payment_amount,
            "payment_method": method,
            "status": "SUCCESS",
            "gateway_fee": gateway_fee,
            "timestamp": created_at
        })
        
        # 3. SETTLEMENT MISMATCH: Bank received less or more than payment - fee
        if i in settle_mismatch_indices:
            settle_shortfall = random.choice([250.0, 480.0, 750.0, 1200.0])
            settled_amount = max(0.0, round(payment_amount - gateway_fee - settle_shortfall, 2))
        else:
            settled_amount = round(payment_amount - gateway_fee, 2)
            
        settle_id = f"set_rzp_{i:04d}"
        settlements.append({
            "settlement_id": settle_id,
            "payment_id": pay_id,
            "order_id": order_id,
            "settled_amount": settled_amount,
            "utr_number": f"UTR_RZP_{random.randint(10000000, 99999999)}",
            "bank_status": "SETTLED",
            "settlement_date": (datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S") + timedelta(days=1)).strftime("%Y-%m-%d")
        })
        
        # 4. DUPLICATE PAYMENT: Customer paid twice on network retry
        if i in duplicate_indices:
            dup_pay_id = f"pay_rzp_dup_{i:04d}a{random.randint(10, 99)}"
            payments.append({
                "payment_id": dup_pay_id,
                "order_id": order_id,
                "payment_amount": amount,
                "payment_method": method,
                "status": "SUCCESS",
                "gateway_fee": gateway_fee,
                "timestamp": (datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S") + timedelta(minutes=random.randint(2, 15))).strftime("%Y-%m-%d %H:%M:%S")
            })
            # Duplicate payment also entered settlement batch
            settlements.append({
                "settlement_id": f"set_rzp_dup_{i:04d}",
                "payment_id": dup_pay_id,
                "order_id": order_id,
                "settled_amount": round(amount - gateway_fee, 2),
                "utr_number": f"UTR_RZP_DUP_{random.randint(10000000, 99999999)}",
                "bank_status": "SETTLED",
                "settlement_date": (datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S") + timedelta(days=1)).strftime("%Y-%m-%d")
            })

    # 5. UNKNOWN PAYMENTS: Payments captured on Razorpay with orphan/missing Order IDs in ERP
    unknown_count = max(3, int(base_order_count * 0.03))
    for k in range(1, unknown_count + 1):
        orphan_order_id = f"ORD_ORPHAN_{8000 + k}"
        orphan_amount = float(random.choice([1500, 2400, 3500, 4800, 6200]))
        orphan_method = random.choice(payment_methods)
        orphan_pay_id = f"pay_rzp_unknown_{k:03d}"
        orphan_fee = round(orphan_amount * 0.02, 2)
        orphan_date = (now - timedelta(days=random.randint(2, 10))).strftime("%Y-%m-%d %H:%M:%S")
        
        payments.append({
            "payment_id": orphan_pay_id,
            "order_id": orphan_order_id,
            "payment_amount": orphan_amount,
            "payment_method": orphan_method,
            "status": "SUCCESS",
            "gateway_fee": orphan_fee,
            "timestamp": orphan_date
        })
        
        settlements.append({
            "settlement_id": f"set_rzp_unk_{k:03d}",
            "payment_id": orphan_pay_id,
            "order_id": orphan_order_id,
            "settled_amount": round(orphan_amount - orphan_fee, 2),
            "utr_number": f"UTR_RZP_UNK_{random.randint(10000000, 99999999)}",
            "bank_status": "SETTLED",
            "settlement_date": (datetime.strptime(orphan_date, "%Y-%m-%d %H:%M:%S") + timedelta(days=1)).strftime("%Y-%m-%d")
        })

    orders_df = pd.DataFrame(orders)
    payments_df = pd.DataFrame(payments)
    settlements_df = pd.DataFrame(settlements)
    
    return orders_df, payments_df, settlements_df
