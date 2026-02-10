"""
Database module for SQLite operations
Handles all database connections and table creation
"""

import sqlite3
import os
import sys

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import DATABASE_PATH

# Database file path from config
DB_PATH = DATABASE_PATH

def get_connection():
    """
    Create and return a database connection
    
    Returns:
        sqlite3.Connection: Database connection object
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

def initialize_database():
    """
    Initialize database and create all required tables
    This function is called when the app starts
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create feedback table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            feedback_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Create features table (clusters)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            feature_name TEXT NOT NULL,
            cluster_id INTEGER,
            reach INTEGER DEFAULT 0,
            impact INTEGER DEFAULT 0,
            confidence INTEGER DEFAULT 80,
            effort INTEGER DEFAULT 0,
            rice_score REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Create feedback_feature mapping table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback_feature_mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feedback_id INTEGER NOT NULL,
            feature_id INTEGER NOT NULL,
            FOREIGN KEY (feedback_id) REFERENCES feedback (id),
            FOREIGN KEY (feature_id) REFERENCES features (id)
        )
    """)
    
    conn.commit()
    conn.close()
    
    print(f"✅ Database initialized successfully at: {DB_PATH}")

# ============================================
# USER OPERATIONS
# ============================================

def create_user(name, email, hashed_password):
    """
    Create a new user in the database
    
    Args:
        name (str): User's full name
        email (str): User's email (must be unique)
        hashed_password (str): Bcrypt hashed password
        
    Returns:
        tuple: (success: bool, message: str, user_id: int or None)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return False, "Email already exists", None
        
        # Insert new user
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, hashed_password)
        )
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return True, "User created successfully", user_id
        
    except Exception as e:
        return False, f"Error creating user: {str(e)}", None

def get_user_by_email(email):
    """
    Retrieve user by email
    
    Args:
        email (str): User's email
        
    Returns:
        dict or None: User data if found, None otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, name, email, password, created_at FROM users WHERE email = ?",
            (email,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "password": row[3],
                "created_at": row[4]
            }
        return None
        
    except Exception as e:
        print(f"Error fetching user: {str(e)}")
        return None

def get_user_by_id(user_id):
    """
    Retrieve user by ID
    
    Args:
        user_id (int): User's ID
        
    Returns:
        dict or None: User data if found, None otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, name, email, created_at FROM users WHERE id = ?",
            (user_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "created_at": row[3]
            }
        return None
        
    except Exception as e:
        print(f"Error fetching user: {str(e)}")
        return None

# ============================================
# FEEDBACK OPERATIONS
# ============================================

def create_feedback(user_id, feedback_text):
    """
    Create a new feedback entry
    
    Args:
        user_id (int): ID of the user submitting feedback
        feedback_text (str): The feedback content
        
    Returns:
        tuple: (success: bool, message: str, feedback_id: int or None)
    """
    try:
        if not feedback_text or not feedback_text.strip():
            return False, "Feedback text cannot be empty", None
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO feedback (user_id, feedback_text) VALUES (?, ?)",
            (user_id, feedback_text.strip())
        )
        
        feedback_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return True, "Feedback added successfully", feedback_id
        
    except Exception as e:
        return False, f"Error adding feedback: {str(e)}", None

def create_feedback_batch(user_id, feedback_list):
    """
    Create multiple feedback entries at once
    
    Args:
        user_id (int): ID of the user submitting feedback
        feedback_list (list): List of feedback text strings
        
    Returns:
        tuple: (success: bool, message: str, count: int)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Filter out empty feedback
        valid_feedback = [f.strip() for f in feedback_list if f and f.strip()]
        
        if not valid_feedback:
            conn.close()
            return False, "No valid feedback to import", 0
        
        # Insert all feedback
        cursor.executemany(
            "INSERT INTO feedback (user_id, feedback_text) VALUES (?, ?)",
            [(user_id, feedback) for feedback in valid_feedback]
        )
        
        count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return True, f"Successfully imported {count} feedback entries", count
        
    except Exception as e:
        return False, f"Error importing feedback: {str(e)}", 0

def get_user_feedback(user_id, limit=None):
    """
    Retrieve all feedback for a specific user
    
    Args:
        user_id (int): User's ID
        limit (int, optional): Maximum number of feedback to return
        
    Returns:
        list: List of feedback dictionaries
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT id, feedback_text, created_at 
            FROM feedback 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, (user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        feedback_list = []
        for row in rows:
            feedback_list.append({
                "id": row[0],
                "feedback_text": row[1],
                "created_at": row[2]
            })
        
        return feedback_list
        
    except Exception as e:
        print(f"Error fetching feedback: {str(e)}")
        return []

def get_feedback_count(user_id):
    """
    Get total count of feedback for a user
    
    Args:
        user_id (int): User's ID
        
    Returns:
        int: Number of feedback entries
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT COUNT(*) FROM feedback WHERE user_id = ?",
            (user_id,)
        )
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
        
    except Exception as e:
        print(f"Error counting feedback: {str(e)}")
        return 0

def delete_feedback(feedback_id, user_id):
    """
    Delete a feedback entry (only if it belongs to the user)
    
    Args:
        feedback_id (int): Feedback ID to delete
        user_id (int): User's ID (for security)
        
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verify ownership before deleting
        cursor.execute(
            "DELETE FROM feedback WHERE id = ? AND user_id = ?",
            (feedback_id, user_id)
        )
        
        if cursor.rowcount == 0:
            conn.close()
            return False, "Feedback not found or unauthorized"
        
        conn.commit()
        conn.close()
        
        return True, "Feedback deleted successfully"
        
    except Exception as e:
        return False, f"Error deleting feedback: {str(e)}"

# ============================================
# FEATURE OPERATIONS (Clustering Results)
# ============================================

def clear_user_features(user_id):
    """
    Delete all existing features for a user
    Used before running new clustering
    
    Args:
        user_id (int): User's ID
        
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM features WHERE user_id = ?",
            (user_id,)
        )
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return True, f"Cleared {deleted_count} existing features"
        
    except Exception as e:
        return False, f"Error clearing features: {str(e)}"

def create_feature(user_id, feature_name, reach):
    """
    Create a new feature from clustering
    
    Args:
        user_id (int): User's ID
        feature_name (str): Name of the feature (from representative feedback)
        reach (int): Number of feedback items in this cluster
        
    Returns:
        tuple: (success: bool, message: str, feature_id: int or None)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO features (user_id, feature_name, reach) VALUES (?, ?, ?)",
            (user_id, feature_name, reach)
        )
        
        feature_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return True, "Feature created", feature_id
        
    except Exception as e:
        return False, f"Error creating feature: {str(e)}", None

def get_user_features(user_id):
    """
    Retrieve all features for a user
    
    Args:
        user_id (int): User's ID
        
    Returns:
        list: List of feature dictionaries
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, feature_name, reach, impact, confidence, effort, rice_score, created_at
            FROM features
            WHERE user_id = ?
            ORDER BY reach DESC
        """, (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        features = []
        for row in rows:
            features.append({
                "id": row[0],
                "feature_name": row[1],
                "reach": row[2],
                "impact": row[3],
                "confidence": row[4],
                "effort": row[5],
                "rice_score": row[6],
                "created_at": row[7]
            })
        
        return features
        
    except Exception as e:
        print(f"Error fetching features: {str(e)}")
        return []

def get_feature_count(user_id):
    """
    Get total count of features for a user
    
    Args:
        user_id (int): User's ID
        
    Returns:
        int: Number of features
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT COUNT(*) FROM features WHERE user_id = ?",
            (user_id,)
        )
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
        
    except Exception as e:
        print(f"Error counting features: {str(e)}")
        return 0

def update_feature_score(feature_id, user_id, impact, effort, confidence, rice_score):
    """
    Update RICE scoring for a feature
    
    Args:
        feature_id (int): Feature's ID
        user_id (int): User's ID (for security)
        impact (int): Impact score (1-5)
        effort (int): Effort score (1-5)
        confidence (int): Confidence percentage (0-100)
        rice_score (float): Calculated RICE score
        
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Update only if feature belongs to user
        cursor.execute("""
            UPDATE features 
            SET impact = ?, effort = ?, confidence = ?, rice_score = ?
            WHERE id = ? AND user_id = ?
        """, (impact, effort, confidence, rice_score, feature_id, user_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return False, "Feature not found or unauthorized"
        
        conn.commit()
        conn.close()
        
        return True, "Feature scored successfully"
        
    except Exception as e:
        return False, f"Error updating feature score: {str(e)}"

def get_prioritized_features(user_id, limit=None):
    """
    Get features sorted by RICE score (highest first)
    Only returns features that have been scored
    
    Args:
        user_id (int): User's ID
        limit (int, optional): Maximum number to return
        
    Returns:
        list: List of feature dictionaries sorted by RICE score
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT id, feature_name, reach, impact, confidence, effort, rice_score, created_at
            FROM features
            WHERE user_id = ? AND rice_score IS NOT NULL AND rice_score > 0
            ORDER BY rice_score DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, (user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        features = []
        for row in rows:
            features.append({
                "id": row[0],
                "feature_name": row[1],
                "reach": row[2],
                "impact": row[3],
                "confidence": row[4],
                "effort": row[5],
                "rice_score": row[6],
                "created_at": row[7]
            })
        
        return features
        
    except Exception as e:
        print(f"Error fetching prioritized features: {str(e)}")
        return []

if __name__ == "__main__":
    # Initialize database when this module is run directly
    initialize_database()
