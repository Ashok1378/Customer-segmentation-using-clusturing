# 🎯 Customer Segmentation & Clustering

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green?logo=fastapi)
![React](https://img.shields.io/badge/React-18-blue?logo=react)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4-orange?logo=scikit-learn)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

A full-stack **Machine Learning web application** for segmenting customers using unsupervised clustering algorithms. Upload your customer CSV, choose features and algorithm, and instantly explore interactive cluster visualisations with downloadable results.

---

## 📌 Problem Statement

Modern businesses accumulate vast amounts of customer data but struggle to derive actionable insights from raw records. Without segmentation, marketing campaigns are untargeted, budgets are wasted, and customer experience suffers. Identifying natural groupings within a customer base — based on demographic and behavioural attributes — enables personalised strategies for each segment.

---

## 🎯 Objective

- Automatically discover natural customer segments from structured data.
- Support multiple clustering algorithms so analysts can compare results.
- Provide a browser-based UI that requires no ML expertise to operate.
- Expose a documented REST API for programmatic access and integration.
- Allow export of cluster labels for downstream CRM or BI tooling.

---

## 🛠️ Technologies

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.10+ | Core language |
| FastAPI | 0.110+ | REST API framework |
| scikit-learn | 1.4+ | Clustering algorithms & metrics |
| pandas | 2.2+ | Data loading & preprocessing |
| NumPy | 1.26+ | Numerical computation |
| Matplotlib / Seaborn | 3.8+ / 0.13+ | Plot generation |
| Joblib | 1.3+ | Model serialisation |
| Uvicorn | 0.29+ | ASGI server |
| python-multipart | 0.0.9+ | File upload handling |

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18 | UI framework |
| Vite | 5 | Build tool & dev server |
| Plotly.js | 5.x | Interactive charts |
| Axios | 1.x | HTTP client |
| Tailwind CSS | 3.x | Utility-first styling |
| React Router | 6.x | Client-side routing |

---

## 🤖 Algorithms

### K-Means Clustering
K-Means partitions data into **K** non-overlapping clusters by iteratively assigning each point to the nearest centroid and recomputing centroids until convergence.

- **Complexity**: O(n · k · i · d) — fast for large datasets
- **Best for**: Well-separated, roughly spherical clusters
- **Hyperparameter**: Number of clusters K (selected via Elbow method / Silhouette analysis)
- **Initialisation**: K-Means++ (avoids poor centroid initialisation)

### Hierarchical Clustering (Agglomerative)
Builds a **dendrogram** by successively merging the two closest clusters (bottom-up). The tree is cut at a chosen level to produce flat clusters.

- **Linkage criteria**: Ward (minimises within-cluster variance), Average, Complete
- **Best for**: Datasets where the number of clusters is unknown; produces interpretable dendrogram
- **Complexity**: O(n³) — suitable for small-medium datasets
- **No need** to pre-specify K; the dendrogram guides selection

### DBSCAN (Density-Based Spatial Clustering of Applications with Noise)
Groups points that are closely packed together and marks points in low-density regions as **noise/outliers**.

- **Parameters**: `eps` (neighbourhood radius), `min_samples` (minimum points per core point)
- **Best for**: Arbitrarily shaped clusters; robust to outliers
- **Advantage**: Automatically determines the number of clusters
- **Limitation**: Struggles with varying density clusters

---

## 📊 Evaluation Metrics

| Metric | Range | Interpretation |
|--------|-------|----------------|
| **Silhouette Score** | -1 to +1 | Higher = better-defined clusters. >0.5 is good. |
| **Davies-Bouldin Index** | 0 to ∞ | Lower = better separation. 0 is ideal. |
| **WCSS (Inertia)** | 0 to ∞ | Lower = tighter clusters. Used in Elbow method. |
| **Calinski-Harabasz** | 0 to ∞ | Higher = denser, well-separated clusters. |

---

## 🔄 ML Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                        ML PIPELINE                              │
│                                                                 │
│  ┌──────────┐    ┌──────────────┐    ┌─────────────────────┐   │
│  │  Upload  │───►│  Preprocess  │───►│  Feature Selection  │   │
│  │  CSV     │    │  • Impute    │    │  • Drop CustomerID  │   │
│  └──────────┘    │  • Clip      │    │  • Select numerics  │   │
│                  │  • Dedup     │    └──────────┬──────────┘   │
│                  └──────────────┘               │              │
│                                                 ▼              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  Scaling (StandardScaler)                │   │
│  └──────────────────────────────┬────────────────────────  ┘   │
│                                 │                              │
│              ┌──────────────────┼──────────────────┐          │
│              ▼                  ▼                  ▼          │
│        ┌──────────┐      ┌──────────┐      ┌──────────┐      │
│        │ K-Means  │      │  Hier.   │      │  DBSCAN  │      │
│        │          │      │ Cluster  │      │          │      │
│        └────┬─────┘      └────┬─────┘      └────┬─────┘      │
│             └────────────────┬┘────────────────-┘             │
│                              ▼                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │             Evaluation Metrics Computation               │   │
│  │     Silhouette · Davies-Bouldin · WCSS · CH-Index        │   │
│  └──────────────────────────────┬──────────────────────────┘   │
│                                 │                              │
│              ┌──────────────────┼──────────────────┐          │
│              ▼                  ▼                  ▼          │
│        ┌──────────┐      ┌──────────┐      ┌──────────┐      │
│        │  2D PCA  │      │ Cluster  │      │ Download │      │
│        │  Plot    │      │  Stats   │      │   CSV    │      │
│        └──────────┘      └──────────┘      └──────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Installation (Windows)

### Prerequisites
- Python 3.10 or higher — [python.org](https://www.python.org/downloads/)
- Node.js 18+ & npm — [nodejs.org](https://nodejs.org/)
- Git — [git-scm.com](https://git-scm.com/)

### Step-by-Step

**Step 1 — Clone the repository**
```powershell
git clone https://github.com/your-username/Customer_Segmentation_Clustering.git
cd Customer_Segmentation_Clustering
```

**Step 2 — Set up Python virtual environment**
```powershell
cd backend
python -m venv venv
venv\Scripts\activate
```

**Step 3 — Install Python dependencies**
```powershell
pip install -r requirements.txt
```

**Step 4 — Install Node dependencies**
```powershell
cd ..\frontend
npm install
```

---

## ▶️ Running the Backend

```powershell
# From project root
cd backend
venv\Scripts\activate
python run.py
```

The API server starts at **http://localhost:8000**  
Interactive API docs: **http://localhost:8000/docs**

---

## ▶️ Running the Frontend

```powershell
# From project root
cd frontend
npm run dev
```

The React app starts at **http://localhost:5173**

---

## ⚡ Quick Start (Both Services)

Double-click **`start_project.bat`** in the project root. It will:
1. Verify Python and Node.js installations
2. Create and populate the Python virtual environment
3. Install frontend dependencies
4. Launch backend and frontend in separate terminal windows

---

## 📋 Dataset Format

Your CSV must contain at minimum these columns:

| Column | Type | Description | Valid Range |
|--------|------|-------------|-------------|
| `CustomerID` | string | Unique customer identifier | Any |
| `Age` | integer | Customer age in years | 0 – 120 |
| `Gender` | string | Customer gender | Male / Female / Other |
| `AnnualIncome` | float | Annual income in USD | ≥ 0 |
| `SpendingScore` | float | Spending behaviour score | 0 – 100 |
| `PurchaseFrequency` | float | Purchases per year | ≥ 0 |

Additional numerical columns are automatically detected and made available for feature selection.

**Constraints:**
- Minimum 10 rows
- Maximum file size: 50 MB
- Missing values → median imputation
- Out-of-range values → clipped to valid range
- Duplicate rows → removed

---

## 🔌 API Documentation

Full interactive documentation available at **http://localhost:8000/docs** (Swagger UI) and **http://localhost:8000/redoc** (ReDoc).

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check — returns API status |
| `GET` | `/health` | Detailed health information |
| `POST` | `/upload` | Upload a CSV file; returns preview & column info |
| `POST` | `/cluster` | Run clustering with specified algorithm & params |
| `GET` | `/results/{job_id}` | Retrieve results for a completed clustering job |
| `GET` | `/results/{job_id}/download` | Download labelled CSV for a job |
| `GET` | `/results/{job_id}/plot` | Get PCA scatter plot image |
| `DELETE` | `/results/{job_id}` | Delete a clustering job and its artifacts |
| `GET` | `/algorithms` | List available algorithms and their parameters |
| `GET` | `/metrics` | Describe all available evaluation metrics |

### Example Request — Upload

```bash
curl -X POST "http://localhost:8000/upload" \
     -H "accept: application/json" \
     -F "file=@data/sample_customer_data.csv"
```

### Example Request — Cluster

```bash
curl -X POST "http://localhost:8000/cluster" \
     -H "Content-Type: application/json" \
     -d '{
           "job_id": "abc123",
           "algorithm": "kmeans",
           "n_clusters": 5,
           "features": ["Age", "AnnualIncome", "SpendingScore", "PurchaseFrequency"]
         }'
```

---

## 📁 Project Structure

```
Customer_Segmentation_Clustering/
│
├── 📄 README.md                    ← This file
├── 📄 .gitignore
├── 📄 start_project.bat            ← One-click startup script
│
├── 📁 data/
│   ├── 📄 sample_customer_data.csv ← 200-row sample dataset
│   └── 📄 README.md                ← Dataset documentation
│
├── 📁 backend/
│   ├── 📄 run.py                   ← Entry point (uvicorn launcher)
│   ├── 📄 requirements.txt         ← Python dependencies
│   │
│   ├── 📁 app/
│   │   ├── 📄 main.py              ← FastAPI app & router registration
│   │   ├── 📄 config.py            ← App configuration & constants
│   │   │
│   │   ├── 📁 routers/
│   │   │   ├── 📄 upload.py        ← /upload endpoint
│   │   │   ├── 📄 cluster.py       ← /cluster endpoint
│   │   │   └── 📄 results.py       ← /results endpoints
│   │   │
│   │   ├── 📁 services/
│   │   │   ├── 📄 preprocessing.py ← Data cleaning & scaling
│   │   │   ├── 📄 clustering.py    ← Algorithm implementations
│   │   │   ├── 📄 evaluation.py    ← Metrics computation
│   │   │   └── 📄 visualisation.py ← Plot generation
│   │   │
│   │   ├── 📁 models/
│   │   │   └── 📄 schemas.py       ← Pydantic request/response models
│   │   │
│   │   └── 📁 utils/
│   │       ├── 📄 file_utils.py    ← File I/O helpers
│   │       └── 📄 logger.py        ← Logging configuration
│   │
│   ├── 📁 uploads/                 ← Uploaded CSV files (gitignored)
│   │   └── 📄 .gitkeep
│   ├── 📁 models/                  ← Saved .joblib models (gitignored)
│   │   └── 📄 .gitkeep
│   └── 📁 outputs/                 ← Generated plots & CSVs (gitignored)
│       └── 📄 .gitkeep
│
└── 📁 frontend/
    ├── 📄 package.json
    ├── 📄 vite.config.js
    ├── 📄 tailwind.config.js
    ├── 📄 index.html
    │
    └── 📁 src/
        ├── 📄 main.jsx              ← React entry point
        ├── 📄 App.jsx               ← Root component & routing
        ├── 📄 index.css             ← Global styles
        │
        ├── 📁 pages/
        │   ├── 📄 HomePage.jsx      ← Landing / upload page
        │   ├── 📄 ClusterPage.jsx   ← Algorithm config & run page
        │   └── 📄 ResultsPage.jsx   ← Visualisations & export page
        │
        ├── 📁 components/
        │   ├── 📄 FileUpload.jsx    ← Drag-and-drop uploader
        │   ├── 📄 AlgorithmPanel.jsx← Parameter controls
        │   ├── 📄 ClusterPlot.jsx   ← Plotly scatter chart
        │   ├── 📄 MetricsCard.jsx   ← Evaluation metric display
        │   ├── 📄 ClusterTable.jsx  ← Per-cluster statistics table
        │   └── 📄 Navbar.jsx        ← Top navigation bar
        │
        ├── 📁 services/
        │   └── 📄 api.js            ← Axios API calls
        │
        └── 📁 hooks/
            └── 📄 useCluster.js     ← Custom React hook for clustering flow
```

---

## ✨ Features

- **Multi-algorithm support**: K-Means, Hierarchical (Agglomerative), and DBSCAN
- **Drag-and-drop CSV upload** with instant schema validation and data preview
- **Dynamic feature selection**: choose which columns to use for clustering
- **Hyperparameter controls**: sliders and inputs for K, linkage, eps, min_samples
- **Elbow method chart** to assist optimal K selection for K-Means
- **Interactive 2D PCA scatter plot** with colour-coded clusters (Plotly)
- **Per-cluster statistics**: count, mean, std for all features
- **Evaluation dashboard**: Silhouette, Davies-Bouldin, WCSS, Calinski-Harabasz
- **Export labelled CSV**: download your original data with cluster labels appended
- **Swagger / ReDoc API docs** auto-generated by FastAPI
- **Responsive UI**: works on desktop and tablet viewports
- **One-click startup** via `start_project.bat`

---

## 🔧 Troubleshooting

### `python` not recognised
**Error**: `'python' is not recognized as an internal or external command`  
**Fix**: Install Python from python.org and ensure "Add Python to PATH" is checked during installation. Alternatively use `py` instead of `python`.

### `node` not recognised
**Error**: `'node' is not recognized as an internal or external command`  
**Fix**: Install Node.js from nodejs.org and restart your terminal.

### Port 8000 already in use
**Error**: `[Errno 10048] Only one usage of each socket address`  
**Fix**: Kill the process using port 8000:
```powershell
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Port 5173 already in use
**Fix**: Kill the process or change the port in `vite.config.js`:
```js
server: { port: 5174 }
```

### CORS error in browser
**Error**: `Access to XMLHttpRequest blocked by CORS policy`  
**Fix**: Ensure the backend `config.py` includes `http://localhost:5173` in `ALLOWED_ORIGINS`.

### `pip install` fails on Windows
**Fix**: Upgrade pip first:
```powershell
python -m pip install --upgrade pip
```
For `scikit-learn` build errors, install the [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/).

### Upload returns 422 Unprocessable Entity
**Cause**: Missing required columns or wrong data types.  
**Fix**: Check your CSV matches the required schema in the [Dataset Format](#-dataset-format) table.

### Silhouette score not computed
**Cause**: DBSCAN produced only 1 cluster or all noise points.  
**Fix**: Decrease `eps` or decrease `min_samples` to allow more clusters to form.

---

## 📸 Screenshots

> _Screenshots will be added after the first production deployment._

| View | Description |
|------|-------------|
| Home / Upload | Drag-and-drop file upload with data preview table |
| Cluster Config | Algorithm selector, feature checkboxes, hyperparameter sliders |
| Results — Plot | PCA scatter plot with colour-coded cluster assignments |
| Results — Metrics | Silhouette, Davies-Bouldin, WCSS metric cards |
| Results — Table | Per-cluster descriptive statistics |

---

## 📜 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request
