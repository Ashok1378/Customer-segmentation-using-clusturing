"""
Script to generate sample_customer_data.csv with 500 realistic customer records.
"""
import csv
import random
import math

random.seed(42)

def generate_customers(n=500):
    customers = []
    segments = [
        # (income_range, spending_range, freq_range, age_range)
        {"name": "High Value",     "income": (70, 120), "spending": (65, 95), "freq": (15, 40), "age": (25, 55)},
        {"name": "Budget",         "income": (20, 45),  "spending": (10, 40), "freq": (3,  12), "age": (30, 65)},
        {"name": "Frequent",       "income": (40, 75),  "spending": (55, 80), "freq": (20, 50), "age": (20, 40)},
        {"name": "Low Engagement", "income": (30, 60),  "spending": (5,  30), "freq": (1,  8),  "age": (45, 70)},
        {"name": "Potential",      "income": (65, 100), "spending": (15, 45), "freq": (5,  15), "age": (35, 60)},
    ]

    genders = ["Male", "Female"]
    segment_sizes = [120, 110, 100, 90, 80]  # total 500

    customer_id = 1
    for seg, size in zip(segments, segment_sizes):
        for _ in range(size):
            income_lo, income_hi = seg["income"]
            spend_lo, spend_hi = seg["spending"]
            freq_lo, freq_hi = seg["freq"]
            age_lo, age_hi = seg["age"]

            age = random.randint(age_lo, age_hi)
            gender = random.choice(genders)
            annual_income = round(random.uniform(income_lo, income_hi), 1)
            spending_score = random.randint(spend_lo, spend_hi)
            purchase_frequency = random.randint(freq_lo, freq_hi)

            # Introduce ~8% missing values
            if random.random() < 0.03:
                annual_income = None
            if random.random() < 0.02:
                spending_score = None
            if random.random() < 0.02:
                age = None
            if random.random() < 0.01:
                purchase_frequency = None

            customers.append({
                "CustomerID": customer_id,
                "Age": age,
                "Gender": gender,
                "AnnualIncome": annual_income,
                "SpendingScore": spending_score,
                "PurchaseFrequency": purchase_frequency,
            })
            customer_id += 1

    random.shuffle(customers)
    return customers


def main():
    customers = generate_customers(500)
    fieldnames = ["CustomerID", "Age", "Gender", "AnnualIncome", "SpendingScore", "PurchaseFrequency"]
    with open("sample_customer_data.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(customers)
    print(f"Generated {len(customers)} customer records.")


if __name__ == "__main__":
    main()
