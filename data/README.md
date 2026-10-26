# Dataset Information

## Sample Dataset
`sample_customer_data.csv` contains 200 synthetic customer records.

## Required Columns
| Column | Type | Description | Valid Range |
|--------|------|-------------|-------------|
| CustomerID | string | Unique identifier | Any |
| Age | integer | Customer age in years | 0-120 |
| Gender | string | Customer gender | Male/Female/Other |
| AnnualIncome | float | Annual income in USD | >= 0 |
| SpendingScore | float | Spending behavior score | 0-100 |
| PurchaseFrequency | float | Purchases per year | >= 0 |

## Optional Columns
You may include additional numerical columns. They will be available for feature selection.

## Uploading Custom Data
1. Ensure your CSV has at least the required columns.
2. Missing values will be imputed automatically.
3. Invalid values will be clipped to valid ranges.
4. Duplicates will be removed.

## Notes
- CustomerID is not used in clustering.
- Minimum 10 rows required.
- Maximum file size: 50MB.
