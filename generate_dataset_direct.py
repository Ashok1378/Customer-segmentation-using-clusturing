import csv
import random

random.seed(42)

rows = []

# Cluster 1: Young High Spenders (100 rows)
# Age: 20-31, Income: 35k-65k, Spending: 75-98, Frequency: 28-48
for _ in range(100):
    rows.append({
        "Age": random.randint(20, 31),
        "Gender": random.choice(["Male", "Female"]),
        "AnnualIncome": random.randint(35000, 65000),
        "SpendingScore": random.randint(75, 98),
        "PurchaseFrequency": random.randint(28, 48),
    })

# Cluster 2: Affluent High Rollers (100 rows)
# Age: 36-54, Income: 90k-148k, Spending: 70-96, Frequency: 20-35
for _ in range(100):
    rows.append({
        "Age": random.randint(36, 54),
        "Gender": random.choice(["Male", "Female"]),
        "AnnualIncome": random.randint(90000, 148000),
        "SpendingScore": random.randint(70, 96),
        "PurchaseFrequency": random.randint(20, 35),
    })

# Cluster 3: Conservative Wealthy Savers (100 rows)
# Age: 46-68, Income: 85k-140k, Spending: 10-35, Frequency: 5-15
for _ in range(100):
    rows.append({
        "Age": random.randint(46, 68),
        "Gender": random.choice(["Male", "Female"]),
        "AnnualIncome": random.randint(85000, 140000),
        "SpendingScore": random.randint(10, 35),
        "PurchaseFrequency": random.randint(5, 15),
    })

# Cluster 4: Budget Seekers (100 rows)
# Age: 22-52, Income: 18k-38k, Spending: 12-40, Frequency: 4-14
for _ in range(100):
    rows.append({
        "Age": random.randint(22, 52),
        "Gender": random.choice(["Male", "Female"]),
        "AnnualIncome": random.randint(18000, 38000),
        "SpendingScore": random.randint(12, 40),
        "PurchaseFrequency": random.randint(4, 14),
    })

# Cluster 5: Steady Middle-Class Regulars (100 rows)
# Age: 28-62, Income: 45k-75k, Spending: 42-66, Frequency: 15-28
for _ in range(100):
    rows.append({
        "Age": random.randint(28, 62),
        "Gender": random.choice(["Male", "Female"]),
        "AnnualIncome": random.randint(45000, 75000),
        "SpendingScore": random.randint(42, 66),
        "PurchaseFrequency": random.randint(15, 28),
    })

# Shuffle rows so clusters are naturally mixed
random.shuffle(rows)

# Add CustomerID
for idx, r in enumerate(rows, start=1):
    r["CustomerID"] = f"CUST{idx:04d}"

fieldnames = ["CustomerID", "Age", "Gender", "AnnualIncome", "SpendingScore", "PurchaseFrequency"]

paths = [
    r"c:\Users\HP\Downloads\cinereview (2)\Customer_Segmentation_Clustering\data\supermarket_customer_dataset_500.csv",
    r"c:\Users\HP\Downloads\cinereview (2)\Customer_Segmentation_Clustering\frontend\public\supermarket_customer_dataset_500.csv",
    r"c:\Users\HP\Downloads\supermarket_customer_dataset_500.csv",
]

for p in paths:
    with open(p, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print("Created:", p)

print("Direct CSV generation completed successfully! 500 rows.")
