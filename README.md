# HormoneOS

### Open Research Infrastructure for Longitudinal Women's Hormonal AI

---

## 🔬 Why HormoneOS?

> **Every research group repeatedly spends time integrating heterogeneous women's health datasets before they can even begin training AI models. HormoneOS standardizes this process through a reusable research infrastructure, allowing researchers to focus on scientific discovery instead of data integration. In short: Researchers build AI, not data pipelines.**

---

## ⚠️ The Problem & Research Gap

### The Problem
Longitudinal women's health data—comprising wearable sensor telemetry, daily symptom logs, glucose traces, and hormonal panels—is highly heterogeneous, sparse, and locked inside consumer-facing tracking apps. 

### The Research Gap & Limitations
1. **No Common Schema**: Every clinical study uses its own variable names, sample rates, and file structures, making cross-study model validation and generalization impossible.
2. **Lack of Foundation Representations**: Traditional healthcare models require preprocessing raw sequences for every new downstream task, repeating the feature engineering process.
3. **No Centralized Benchmarking**: There is no standardised way to compare architectures on tasks like cycle phase classification or hormone estimation.

---

## 🧠 Our Scientific Contributions

HormoneOS addresses these challenges through a modular five-tier research infrastructure:

1. **Universal Hormonal Schema (UHS)**: A standardized, JSON-serializable open data specification mapping sensor records, biomarkers, and symptoms.
2. **Hormone State Foundation (HSF)**: A temporal representation engine (GRU + attention) trained to embed raw multivariate sequences into a unified 128-dimensional latent space.
3. **Representation Registry**: A database storage layer enabling quick indexing, alignment, and retrieval of generated embeddings.
4. **Benchmark Center**: An automated framework testing representation performance against downstream research tasks (classification, regression).
5. **Research API**: A robust FastAPI program exposing UHS data ingestion, HSF inference, cohort comparisons, and registry downloads.

---

## 📐 Platform Architecture

```text
    Ingested Datasets (e.g., mcPHASES, Synthetic)
                        ↓
            Universal Hormonal Schema (UHS)
                        ↓
         Hormone State Foundation (HSF) Model
                        ↓
            128-d Reusable Embeddings
                        ↓
    Representation Registry  ⟷  Research API Playground
         ↙             ↓             ↘
Representation   Benchmark Center  Downstream Research Tasks
  Comparison
```

---

## ⚙️ Quick Start (Local Setup)

The project requires **PostgreSQL** and the **`uv`** package manager.

### 1. Database Setup
Ensure PostgreSQL is running locally, then create the database credentials matching `.env`:
```bash
psql -d postgres -c "CREATE ROLE hormoneos WITH LOGIN PASSWORD 'hormoneos' SUPERUSER;"
psql -d postgres -c "CREATE DATABASE hormoneos OWNER hormoneos;"
```

### 2. Backend Installation & Seeding
Navigate to the `backend` folder and use `uv` to initialize the environment and run the database seeds:
```bash
cd backend
# Create Python 3.11 environment (required for PyTorch 2.3.0 support)
uv venv --python 3.11
uv sync

# Run database seeds
uv run scripts/seed_db.py

# Start the FastAPI service
uv run uvicorn app.main:app --reload
```
The Research API will be active on [http://localhost:8000](http://localhost:8000).

### 3. Frontend Installation & Startup
Navigate to the `frontend` directory and start the Next.js development server:
```bash
cd ../frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to access the **Research Workspace**.

---

## 🔮 Future Work & Healthcare Interoperability
- **HL7 FHIR Mapping**: Building native translation schemas to export UHS records directly to FHIR resources (e.g., `Observation`, `DiagnosticReport`) for hospital EHR compatibility.
- **Multimodal Foundation Scale**: Scaling HSF from a GRU architecture to a sequence-to-sequence transformer trained on larger longitudinal cohorts.
- **Federated Registry**: Enabling privacy-preserving decentralized query registries across multiple university research hospitals.

---

## 🧪 Limitations
- **Sequence Length**: Extremely long multi-year longitudinal traces require chunking to avoid memory bottlenecks in recursive layers.
- **Biomarker Availability**: HSF embeddings depend on having at least partial hormonal inputs (e.g., Estrogen, Progesterone) alongside wearable features for high-fidelity representation mapping.
# HormoneOS
