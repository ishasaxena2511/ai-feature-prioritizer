# AI-Powered Feature Prioritization Tool

A web application that helps Product Managers prioritize features using AI-driven clustering and the RICE framework.

## 🎯 Features

- User Authentication
- Feedback Collection (manual input + CSV upload)
- AI-powered clustering of similar feedback
- RICE scoring framework for feature prioritization
- Dashboard with top 5 recommended features

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Backend**: Python
- **AI/NLP**: SentenceTransformers, scikit-learn
- **Database**: SQLite

## 📦 Installation

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

**Note**: The database will be automatically initialized when you first run the application.

## 🚀 Running the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## 📁 Project Structure

```
ai-feature-prioritizer/
│
├── app.py                          # Main Streamlit application
├── config.py                       # Application configuration
├── requirements.txt                # Python dependencies
├── README.md                       # This file
│
├── database/
│   ├── db.py                      # Database operations
│   └── feature_prioritization.db  # SQLite database (created on first run)
│
├── auth/
│   └── auth.py                     # Authentication logic
│
├── feedback/
│   └── feedback_processor.py      # Feedback handling
│
├── ai/
│   └── clustering.py              # NLP clustering
│
├── scoring/
│   └── rice_scoring.py            # RICE framework
│
└── utils/
    └── helpers.py                 # Helper functions
```

## ⚙️ Configuration

All application settings are centralized in `config.py`:

- **DATABASE_PATH**: Location of SQLite database
- **MODEL_NAME**: SentenceTransformer model for embeddings (`all-MiniLM-L6-v2`)
- **DEFAULT_CLUSTER_COUNT**: Default number of clusters (5)
- **MIN_FEEDBACK_FOR_CLUSTERING**: Minimum feedback needed for clustering
- **TOP_FEATURES_COUNT**: Number of top features to display (5)
- **DEFAULT_CONFIDENCE**: Default confidence percentage for RICE (80%)

## 📊 RICE Framework

**RICE Score = (Reach × Impact × Confidence) / Effort**

- **Reach**: Number of users affected
- **Impact**: Impact on users (1-5 scale)
- **Confidence**: Confidence in estimates (0-100%)
- **Effort**: Development effort (1-5 scale)

## 👨‍💼 Author
Isha M Saxena 



