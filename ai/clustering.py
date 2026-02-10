"""
AI Clustering module
Handles text preprocessing, embeddings, and clustering
"""

import numpy as np
from sklearn.cluster import KMeans
from sentence_transformers import SentenceTransformer
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database.db import get_user_feedback, clear_user_features, create_feature
import config

# ============================================
# TEXT PREPROCESSING
# ============================================

def preprocess_text(text):
    """
    Clean and preprocess text for embedding generation
    
    Args:
        text (str): Raw feedback text
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text.strip()

# ============================================
# EMBEDDING GENERATION
# ============================================

# Global model instance (loaded once)
_model = None

def load_model():
    """
    Load SentenceTransformer model
    Uses lazy loading - only loads when first needed
    
    Returns:
        SentenceTransformer: Loaded model
    """
    global _model
    
    if _model is None:
        print(f"Loading model: {config.MODEL_NAME}")
        _model = SentenceTransformer(config.MODEL_NAME)
        print("Model loaded successfully")
    
    return _model

def generate_embeddings(texts):
    """
    Generate embeddings for a list of texts
    
    Args:
        texts (list): List of text strings
        
    Returns:
        np.ndarray: Array of embeddings (shape: [n_texts, embedding_dim])
    """
    if not texts:
        return np.array([])
    
    # Load model
    model = load_model()
    
    # Preprocess texts
    cleaned_texts = [preprocess_text(text) for text in texts]
    
    # Generate embeddings
    embeddings = model.encode(cleaned_texts, show_progress_bar=False)
    
    return embeddings

# ============================================
# CLUSTERING
# ============================================

def cluster_feedback(embeddings, n_clusters=None):
    """
    Cluster embeddings using KMeans
    
    Args:
        embeddings (np.ndarray): Array of embeddings
        n_clusters (int, optional): Number of clusters. 
                                    If None, uses DEFAULT_CLUSTER_COUNT from config
        
    Returns:
        np.ndarray: Array of cluster labels
    """
    if n_clusters is None:
        n_clusters = config.DEFAULT_CLUSTER_COUNT
    
    # Adjust n_clusters if we have fewer feedback items
    n_samples = len(embeddings)
    n_clusters = min(n_clusters, n_samples)
    
    # Run KMeans
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(embeddings)
    
    return labels

# ============================================
# FEATURE NAME GENERATION
# ============================================

def get_representative_text(feedback_texts, cluster_indices):
    """
    Get the most representative text for a cluster
    Uses the shortest text as it's often the most concise
    
    Args:
        feedback_texts (list): List of all feedback texts
        cluster_indices (list): Indices of feedback in this cluster
        
    Returns:
        str: Representative text for the cluster
    """
    if not cluster_indices:
        return "Unnamed Feature"
    
    # Get texts for this cluster
    cluster_texts = [feedback_texts[i] for i in cluster_indices]
    
    # Find shortest text (usually most concise)
    representative = min(cluster_texts, key=len)
    
    # Truncate if too long
    max_length = 100
    if len(representative) > max_length:
        representative = representative[:max_length] + "..."
    
    return representative

def generate_features_from_clusters(feedback_list, labels):
    """
    Generate feature names and calculate reach for each cluster
    
    Args:
        feedback_list (list): List of feedback dictionaries
        labels (np.ndarray): Array of cluster labels
        
    Returns:
        list: List of feature dictionaries with name and reach
    """
    features = []
    
    # Get unique cluster labels
    unique_labels = np.unique(labels)
    
    # Extract feedback texts
    feedback_texts = [f['feedback_text'] for f in feedback_list]
    
    for cluster_id in unique_labels:
        # Get indices of feedback in this cluster
        cluster_indices = np.where(labels == cluster_id)[0].tolist()
        
        # Get representative text for feature name
        feature_name = get_representative_text(feedback_texts, cluster_indices)
        
        # Calculate reach (number of feedback items)
        reach = len(cluster_indices)
        
        features.append({
            'feature_name': feature_name,
            'reach': reach,
            'cluster_id': int(cluster_id)
        })
    
    # Sort by reach (descending)
    features.sort(key=lambda x: x['reach'], reverse=True)
    
    return features

# ============================================
# MAIN CLUSTERING PIPELINE
# ============================================

def run_clustering(user_id):
    """
    Complete clustering pipeline for a user
    
    Steps:
    1. Get user's feedback
    2. Check minimum feedback requirement
    3. Preprocess texts
    4. Generate embeddings
    5. Cluster embeddings
    6. Generate feature names
    7. Clear old features
    8. Save new features to database
    
    Args:
        user_id (int): User's ID
        
    Returns:
        tuple: (success: bool, message: str, feature_count: int)
    """
    try:
        # Step 1: Get user feedback
        feedback_list = get_user_feedback(user_id)
        
        if not feedback_list:
            return False, "No feedback found. Please add feedback first.", 0
        
        # Step 2: Check minimum requirement
        if len(feedback_list) < config.MIN_FEEDBACK_FOR_CLUSTERING:
            return False, f"Not enough feedback to run clustering. Need at least {config.MIN_FEEDBACK_FOR_CLUSTERING} items.", 0
        
        # Step 3: Extract feedback texts
        feedback_texts = [f['feedback_text'] for f in feedback_list]
        
        # Step 4: Generate embeddings
        print(f"Generating embeddings for {len(feedback_texts)} feedback items...")
        embeddings = generate_embeddings(feedback_texts)
        
        if len(embeddings) == 0:
            return False, "Failed to generate embeddings", 0
        
        # Step 5: Cluster feedback
        print(f"Clustering into {config.DEFAULT_CLUSTER_COUNT} groups...")
        labels = cluster_feedback(embeddings)
        
        # Step 6: Generate features from clusters
        features = generate_features_from_clusters(feedback_list, labels)
        
        # Step 7: Clear old features
        clear_user_features(user_id)
        
        # Step 8: Save new features to database
        feature_count = 0
        for feature in features:
            success, message, feature_id = create_feature(
                user_id,
                feature['feature_name'],
                feature['reach']
            )
            if success:
                feature_count += 1
        
        return True, f"Successfully created {feature_count} feature clusters", feature_count
        
    except Exception as e:
        return False, f"Error during clustering: {str(e)}", 0

# ============================================
# CLUSTERING STATISTICS
# ============================================

def get_clustering_stats(user_id):
    """
    Get statistics about clustering readiness
    
    Args:
        user_id (int): User's ID
        
    Returns:
        dict: Statistics dictionary
    """
    from database.db import get_feedback_count, get_feature_count
    
    feedback_count = get_feedback_count(user_id)
    feature_count = get_feature_count(user_id)
    
    return {
        'feedback_count': feedback_count,
        'feature_count': feature_count,
        'can_cluster': feedback_count >= config.MIN_FEEDBACK_FOR_CLUSTERING,
        'min_required': config.MIN_FEEDBACK_FOR_CLUSTERING,
        'has_features': feature_count > 0
    }
