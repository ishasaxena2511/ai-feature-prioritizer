"""
Configuration file for AI Feature Prioritization Tool
Contains all application-wide constants and settings
"""

import os

# ============================================
# DATABASE CONFIGURATION
# ============================================
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "database", "feature_prioritization.db")

# ============================================
# AI/NLP CONFIGURATION
# ============================================
# Sentence Transformer model for generating embeddings
MODEL_NAME = "all-MiniLM-L6-v2"

# Default number of clusters for KMeans
DEFAULT_CLUSTER_COUNT = 5

# Minimum number of feedback items required for clustering
MIN_FEEDBACK_FOR_CLUSTERING = 3

# ============================================
# RICE SCORING CONFIGURATION
# ============================================
# Default confidence percentage if not specified
DEFAULT_CONFIDENCE = 80

# RICE score ranges for priority levels
RICE_HIGH_THRESHOLD = 50
RICE_MEDIUM_THRESHOLD = 20

# ============================================
# UI CONFIGURATION
# ============================================
# Number of top features to display on dashboard
TOP_FEATURES_COUNT = 5

# Maximum feedback text length for display
MAX_FEEDBACK_DISPLAY_LENGTH = 200

# Maximum number of feedback items per user
MAX_FEEDBACK_PER_USER = 2000

# ============================================
# SESSION CONFIGURATION
# ============================================
SESSION_TIMEOUT_HOURS = 24
