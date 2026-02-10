"""
Utility functions
Helper functions used across the application
"""

import re
from datetime import datetime

def clean_text(text):
    """
    Clean and preprocess text for NLP
    
    Args:
        text (str): Raw text input
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters but keep spaces
    text = re.sub(r'[^a-z0-9\s]', '', text)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text

def format_timestamp(timestamp):
    """
    Format timestamp for display
    
    Args:
        timestamp: Database timestamp
        
    Returns:
        str: Formatted date string
    """
    if isinstance(timestamp, str):
        dt = datetime.fromisoformat(timestamp)
    else:
        dt = timestamp
    
    return dt.strftime("%Y-%m-%d %H:%M")

def validate_rice_input(reach, impact, confidence, effort):
    """
    Validate RICE framework inputs
    
    Args:
        reach (int): Number of users affected
        impact (int): Impact score (1-5)
        confidence (int): Confidence percentage (0-100)
        effort (int): Effort score (1-5)
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if reach < 0:
        return False, "Reach must be a positive number"
    
    if impact < 1 or impact > 5:
        return False, "Impact must be between 1 and 5"
    
    if confidence < 0 or confidence > 100:
        return False, "Confidence must be between 0 and 100"
    
    if effort < 1 or effort > 5:
        return False, "Effort must be between 1 and 5"
    
    return True, ""
