"""
Feedback processing module
Handles feedback input, CSV uploads, and storage
"""

import pandas as pd
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database.db import create_feedback, create_feedback_batch, get_user_feedback, get_feedback_count, delete_feedback
import config

# ============================================
# FEEDBACK SUBMISSION
# ============================================

def submit_feedback(user_id, feedback_text):
    """
    Submit a single feedback entry
    
    Args:
        user_id (int): ID of the logged-in user
        feedback_text (str): The feedback content
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Validate input
    if not feedback_text or not feedback_text.strip():
        return False, "Please enter feedback text"
    
    if len(feedback_text.strip()) < 10:
        return False, "Feedback must be at least 10 characters long"
    
    # Check feedback limit
    current_count = get_feedback_count(user_id)
    if current_count >= config.MAX_FEEDBACK_PER_USER:
        return False, f"Feedback limit reached ({config.MAX_FEEDBACK_PER_USER}). Please delete some entries."
    
    # Store in database
    success, message, feedback_id = create_feedback(user_id, feedback_text)
    
    return success, message

# ============================================
# CSV PROCESSING
# ============================================

def validate_csv(df):
    """
    Validate CSV file structure
    
    Args:
        df (pandas.DataFrame): Uploaded CSV data
        
    Returns:
        tuple: (is_valid: bool, message: str, column_name: str or None)
    """
    if df is None or df.empty:
        return False, "CSV file is empty", None
    
    # Check for 'feedback' column (case-insensitive)
    feedback_col = None
    for col in df.columns:
        if col.lower() == 'feedback':
            feedback_col = col
            break
    
    if not feedback_col:
        return False, "CSV must contain a 'feedback' column", None
    
    # Check if column has data
    non_empty = df[feedback_col].notna().sum()
    if non_empty == 0:
        return False, "The 'feedback' column is empty", None
    
    return True, f"Found {non_empty} feedback entries", feedback_col

def process_csv(user_id, uploaded_file):
    """
    Process uploaded CSV file and import feedback
    
    Args:
        user_id (int): ID of the logged-in user
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        tuple: (success: bool, message: str, count: int)
    """
    try:
        # Read CSV file
        df = pd.read_csv(uploaded_file)
        
        # Validate CSV structure
        is_valid, message, feedback_col = validate_csv(df)
        if not is_valid:
            return False, message, 0
        
        # Extract feedback text (remove NaN values)
        feedback_list = df[feedback_col].dropna().astype(str).tolist()
        
        # Filter out very short feedback
        feedback_list = [f for f in feedback_list if len(f.strip()) >= 10]
        
        if not feedback_list:
            return False, "No valid feedback found (minimum 10 characters each)", 0
        
        # Check feedback limit
        current_count = get_feedback_count(user_id)
        if current_count >= config.MAX_FEEDBACK_PER_USER:
            return False, f"Feedback limit reached ({config.MAX_FEEDBACK_PER_USER}). Please delete some entries.", 0
        
        # Check if import would exceed limit
        if current_count + len(feedback_list) > config.MAX_FEEDBACK_PER_USER:
            allowed = config.MAX_FEEDBACK_PER_USER - current_count
            return False, f"Cannot import {len(feedback_list)} items. Only {allowed} slots remaining (limit: {config.MAX_FEEDBACK_PER_USER}).", 0
        
        # Import to database
        success, db_message, count = create_feedback_batch(user_id, feedback_list)
        
        return success, db_message, count
        
    except pd.errors.EmptyDataError:
        return False, "CSV file is empty", 0
    except pd.errors.ParserError:
        return False, "Invalid CSV format", 0
    except Exception as e:
        return False, f"Error processing CSV: {str(e)}", 0

# ============================================
# FEEDBACK RETRIEVAL
# ============================================

def get_all_feedback(user_id):
    """
    Get all feedback for a user
    
    Args:
        user_id (int): ID of the user
        
    Returns:
        list: List of feedback dictionaries
    """
    return get_user_feedback(user_id)

def get_feedback_stats(user_id):
    """
    Get feedback statistics for a user
    
    Args:
        user_id (int): ID of the user
        
    Returns:
        dict: Statistics dictionary
    """
    total_count = get_feedback_count(user_id)
    
    return {
        "total": total_count,
        "ready_for_clustering": total_count >= 3  # Need at least 3 for clustering
    }

# ============================================
# FEEDBACK DELETION
# ============================================

def delete_feedback_item(feedback_id, user_id):
    """
    Delete a feedback entry
    
    Args:
        feedback_id (int): ID of the feedback to delete
        user_id (int): ID of the logged-in user (for security)
        
    Returns:
        tuple: (success: bool, message: str)
    """
    return delete_feedback(feedback_id, user_id)
