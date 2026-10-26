import os
import numpy as np
import pandas as pd

np.random.seed(42)

def generate_customers(n_total=500):
    n_per_cluster = n_total // 5  # 100 per cluster

    clusters = []

    # Cluster 1: Young High Spenders (Tech & Fashion Youth)
    c1_age = np.random.randint(20, 32, n_per_cluster)
    c1_income = np.random.randint(35000, 65000, n_per_cluster)
    c1_spending = np.random.randint(75, 99, n_per_cluster)
    c1_freq = np.random.randint(28, 48, n_per_cluster)
    c1_gender = np.random.choice(["Male", "Female"], n_per_cluster, p=[0.48, 0.52])
    c1 = pd.DataFrame({
        "Age": c1_age, "Gender": c1_gender, "AnnualIncome": c1_income,
        "SpendingScore": c1_spending, "PurchaseFrequency": c1_freq
    })
    clusters.append(c1)

    # Cluster 2: Affluent High Rollers (Wealthy & High Spenders)
    c2_age = np.random.randint(35, 55, n_per_cluster)
    c2_income = np.random.randint(90000, 150000, n_per_cluster)
    c2_spending = np.random.randint(70, 96, n_per_cluster)
    c2_freq = np.random.randint(20, 36, n_per_cluster)
    c2_gender = np.random.choice(["Male", "Female"], n_per_cluster, p=[0.50, 0.50])
    c2 = pd.DataFrame({
        "Age": c2_age, "Gender": c2_gender, "AnnualIncome": c2_income,
        "SpendingScore": c2_spending, "PurchaseFrequency": c2_freq
    })
    clusters.append(c2)

    # Cluster 3: Conservative Wealthy (High Income, Low Spending Savers)
    c3_age = np.random.randint(45, 68, n_per_cluster)
    c3_income = np.random.randint(85000, 140000, n_per_cluster)
    c3_spending = np.random.randint(10, 35, n_per_cluster)
    c3_freq = np.random.randint(5, 16, n_per_cluster)
    c3_gender = np.random.choice(["Male", "Female"], n_per_cluster, p=[0.52, 0.48])
    c3 = pd.DataFrame({
        "Age": c3_age, "Gender": c3_gender, "AnnualIncome": c3_income,
        "SpendingScore": c3_spending, "PurchaseFrequency": c3_freq
    })
    clusters.append(c3)

    # Cluster 4: Budget Seekers (Low Income, Low Spending)
    c4_age = np.random.randint(22, 52, n_per_cluster)
    c4_income = np.random.randint(18000, 38000, n_per_cluster)
    c4_spending = np.random.randint(12, 40, n_per_cluster)
    c4_freq = np.random.randint(4, 15, n_per_cluster)
    c4_gender = np.random.choice(["Male", "Female"], n_per_cluster, p=[0.46, 0.54])
    c4 = pd.DataFrame({
        "Age": c4_age, "Gender": c4_gender, "AnnualIncome": c4_income,
        "SpendingScore": c4_spending, "PurchaseFrequency": c4_freq
    })
    clusters.append(c4)

    # Cluster 5: Steady Middle-Class Regulars (Balanced Spenders)
    c5_age = np.random.randint(28, 62, n_per_cluster)
    c5_income = np.random.randint(45000, 75000, n_per_cluster)
    c5_spending = np.random.randint(42, 66, n_per_cluster)
    c5_freq = np.random.randint(15, 29, n_per_cluster)
    c5_gender = np.random.choice(["Male", "Female"], n_per_cluster, p=[0.49, 0.51])
    c5 = pd.DataFrame({
        "Age": c5_age, "Gender": c5_gender, "AnnualIncome": c5_income,
        "SpendingScore": c5_spending, "PurchaseFrequency": c5_freq
    })
    clusters.append(c5)

    df = pd.concat(clusters, ignore_index=True)
    df = df.sample(frac=1.0, random_state=42).reset_index(drop=True)
    df.insert(0, "CustomerID", [f"CUST{i+1:04d}" for i in range(len(df))])

    return df

df = generate_customers(500)

paths = [
    r"c:\Users\HP\Downloads\cinereview (2)\Customer_Segmentation_Clustering\data\supermarket_customer_dataset_500.csv",
    r"c:\Users\HP\Downloads\cinereview (2)\Customer_Segmentation_Clustering\frontend\public\supermarket_customer_dataset_500.csv",
    r"c:\Users\HP\Downloads\supermarket_customer_dataset_500.csv",
]

for p in paths:
    os.makedirs(os.path.dirname(p), exist_ok=True)
    df.to_csv(p, index=False)
    print(f"Saved: {p}")

print("\nDataset generation completed successfully! Total rows: 500")
