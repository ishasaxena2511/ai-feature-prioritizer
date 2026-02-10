"""
RICE Scoring module
Handles feature scoring using the RICE framework
RICE = (Reach × Impact × Confidence) / Effort
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database.db import update_feature_score, get_user_features, get_prioritized_features
import config

# ============================================
# RICE CALCULATION
# ============================================

def calculate_rice_score(reach, impact, confidence, effort):
    """
    Calculate RICE score
    
    Formula: (Reach × Impact × Confidence) / Effort
    
    Args:
        reach (int): Number of users/feedback items affected
        impact (int): Impact score (1-5)
        confidence (int): Confidence percentage (0-100)
        effort (int): Effort score (1-5)
        
    Returns:
        float: Calculated RICE score
    """
    if effort == 0:
        return 0.0
    
    # Convert confidence from percentage to decimal
    confidence_decimal = confidence / 100.0
    
    # Calculate RICE
    rice_score = (reach * impact * confidence_decimal) / effort
    
    # Round to 2 decimal places
    return round(rice_score, 2)

# ============================================
# INPUT VALIDATION
# ============================================

def validate_impact(impact):
    """
    Validate impact score
    
    Args:
        impact (int): Impact score
        
    Returns:
        tuple: (is_valid: bool, message: str)
    """
    if impact is None:
        return False, "Impact is required"
    
    try:
        impact = int(impact)
    except (ValueError, TypeError):
        return False, "Impact must be a number"
    
    if impact < 1 or impact > 5:
        return False, "Impact must be between 1 and 5"
    
    return True, ""

def validate_effort(effort):
    """
    Validate effort score
    
    Args:
        effort (int): Effort score
        
    Returns:
        tuple: (is_valid: bool, message: str)
    """
    if effort is None:
        return False, "Effort is required"
    
    try:
        effort = int(effort)
    except (ValueError, TypeError):
        return False, "Effort must be a number"
    
    if effort < 1 or effort > 5:
        return False, "Effort must be between 1 and 5"
    
    return True, ""

def validate_confidence(confidence):
    """
    Validate confidence percentage
    
    Args:
        confidence (int): Confidence percentage
        
    Returns:
        tuple: (is_valid: bool, message: str)
    """
    if confidence is None:
        return False, "Confidence is required"
    
    try:
        confidence = int(confidence)
    except (ValueError, TypeError):
        return False, "Confidence must be a number"
    
    if confidence < 0 or confidence > 100:
        return False, "Confidence must be between 0 and 100"
    
    return True, ""

# ============================================
# FEATURE SCORING
# ============================================

def score_feature(feature_id, user_id, reach, impact, effort, confidence=None):
    """
    Score a feature using RICE framework
    
    Args:
        feature_id (int): Feature's ID
        user_id (int): User's ID
        reach (int): Reach (from clustering)
        impact (int): Impact score (1-5)
        effort (int): Effort score (1-5)
        confidence (int, optional): Confidence percentage. 
                                    If None, uses DEFAULT_CONFIDENCE from config
        
    Returns:
        tuple: (success: bool, message: str, rice_score: float or None)
    """
    # Use default confidence if not provided
    if confidence is None:
        confidence = config.DEFAULT_CONFIDENCE
    
    # Validate inputs
    is_valid, message = validate_impact(impact)
    if not is_valid:
        return False, message, None
    
    is_valid, message = validate_effort(effort)
    if not is_valid:
        return False, message, None
    
    is_valid, message = validate_confidence(confidence)
    if not is_valid:
        return False, message, None
    
    # Calculate RICE score
    rice_score = calculate_rice_score(reach, impact, confidence, effort)
    
    # Update database
    success, db_message = update_feature_score(
        feature_id, user_id, impact, effort, confidence, rice_score
    )
    
    if success:
        return True, f"Feature scored: RICE = {rice_score}", rice_score
    else:
        return False, db_message, None

# ============================================
# FEATURE PRIORITIZATION
# ============================================

def get_top_features(user_id, count=None):
    """
    Get top N features by RICE score
    
    Args:
        user_id (int): User's ID
        count (int, optional): Number of features to return.
                               If None, uses TOP_FEATURES_COUNT from config
        
    Returns:
        list: List of top features sorted by RICE score
    """
    if count is None:
        count = config.TOP_FEATURES_COUNT
    
    return get_prioritized_features(user_id, limit=count)

def get_all_scored_features(user_id):
    """
    Get all features that have been scored
    
    Args:
        user_id (int): User's ID
        
    Returns:
        list: List of all scored features sorted by RICE score
    """
    return get_prioritized_features(user_id)

def get_unscored_features(user_id):
    """
    Get features that haven't been scored yet
    
    Args:
        user_id (int): User's ID
        
    Returns:
        list: List of unscored features
    """
    all_features = get_user_features(user_id)
    
    # Filter for features without RICE scores
    unscored = [f for f in all_features if f['rice_score'] is None or f['rice_score'] == 0]
    
    return unscored

def get_scoring_stats(user_id):
    """
    Get statistics about feature scoring
    
    Args:
        user_id (int): User's ID
        
    Returns:
        dict: Statistics dictionary
    """
    all_features = get_user_features(user_id)
    scored_features = get_all_scored_features(user_id)
    
    total_features = len(all_features)
    scored_count = len(scored_features)
    unscored_count = total_features - scored_count
    
    return {
        'total_features': total_features,
        'scored_count': scored_count,
        'unscored_count': unscored_count,
        'has_scored': scored_count > 0,
        'all_scored': unscored_count == 0
    }

# ============================================
# PRIORITY LEVELS
# ============================================

def get_priority_level(rice_score):
    """
    Determine priority level based on RICE score
    
    Args:
        rice_score (float): RICE score
        
    Returns:
        str: Priority level ("High", "Medium", "Low")
    """
    if rice_score >= config.RICE_HIGH_THRESHOLD:
        return "High"
    elif rice_score >= config.RICE_MEDIUM_THRESHOLD:
        return "Medium"
    else:
        return "Low"

def get_priority_color(priority_level):
    """
    Get color for priority level (for UI)
    
    Args:
        priority_level (str): Priority level
        
    Returns:
        str: Color name
    """
    colors = {
        "High": "green",
        "Medium": "orange",
        "Low": "red"
    }
    return colors.get(priority_level, "gray")
