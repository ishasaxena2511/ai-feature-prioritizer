"""
Authentication module
Handles user signup, login, logout, and session management
"""

import bcrypt
import streamlit as st
import re
import sys
import os

# Add parent directory to path to import from other modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database.db import create_user, get_user_by_email, get_user_by_id

# ============================================
# PASSWORD HASHING
# ============================================

def hash_password(password):
    """
    Hash a password using bcrypt
    
    Args:
        password (str): Plain text password
        
    Returns:
        str: Hashed password
    """
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password, hashed_password):
    """
    Verify a password against its hash
    
    Args:
        plain_password (str): Plain text password to verify
        hashed_password (str): Stored hashed password
        
    Returns:
        bool: True if password matches, False otherwise
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )

# ============================================
# INPUT VALIDATION
# ============================================

def validate_email(email):
    """
    Validate email format
    
    Args:
        email (str): Email to validate
        
    Returns:
        tuple: (is_valid: bool, message: str)
    """
    if not email:
        return False, "Email is required"
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False, "Invalid email format"
    
    return True, ""

def validate_password(password):
    """
    Validate password strength
    
    Args:
        password (str): Password to validate
        
    Returns:
        tuple: (is_valid: bool, message: str)
    """
    if not password:
        return False, "Password is required"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    return True, ""

def validate_name(name):
    """
    Validate name input
    
    Args:
        name (str): Name to validate
        
    Returns:
        tuple: (is_valid: bool, message: str)
    """
    if not name or not name.strip():
        return False, "Name is required"
    
    if len(name.strip()) < 2:
        return False, "Name must be at least 2 characters long"
    
    return True, ""

# ============================================
# SESSION MANAGEMENT
# ============================================

def initialize_session_state():
    """
    Initialize session state variables if they don't exist
    """
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
    
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None

def login_user(user_id, name, email):
    """
    Log in a user by setting session state
    
    Args:
        user_id (int): User's database ID
        name (str): User's name
        email (str): User's email
    """
    st.session_state.logged_in = True
    st.session_state.user_id = user_id
    st.session_state.user_name = name
    st.session_state.user_email = email

def logout_user():
    """
    Log out the current user by clearing session state
    """
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.user_email = None

def is_logged_in():
    """
    Check if a user is currently logged in
    
    Returns:
        bool: True if logged in, False otherwise
    """
    return st.session_state.get('logged_in', False)

def get_current_user():
    """
    Get the current logged-in user's information
    
    Returns:
        dict or None: User info if logged in, None otherwise
    """
    if not is_logged_in():
        return None
    
    return {
        'id': st.session_state.user_id,
        'name': st.session_state.user_name,
        'email': st.session_state.user_email
    }

# ============================================
# AUTHENTICATION FUNCTIONS
# ============================================

def signup(name, email, password):
    """
    Register a new user
    
    Args:
        name (str): User's full name
        email (str): User's email
        password (str): User's password
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Validate inputs
    is_valid, message = validate_name(name)
    if not is_valid:
        return False, message
    
    is_valid, message = validate_email(email)
    if not is_valid:
        return False, message
    
    is_valid, message = validate_password(password)
    if not is_valid:
        return False, message
    
    # Hash password
    hashed_password = hash_password(password)
    
    # Create user in database
    success, message, user_id = create_user(name.strip(), email.lower().strip(), hashed_password)
    
    if success:
        return True, "Account created successfully! Please log in."
    else:
        return False, message

def login(email, password):
    """
    Authenticate a user and create session
    
    Args:
        email (str): User's email
        password (str): User's password
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Validate inputs
    if not email or not password:
        return False, "Email and password are required"
    
    # Get user from database
    user = get_user_by_email(email.lower().strip())
    
    if not user:
        return False, "Invalid email or password"
    
    # Verify password
    if not verify_password(password, user['password']):
        return False, "Invalid email or password"
    
    # Create session
    login_user(user['id'], user['name'], user['email'])
    
    return True, f"Welcome back, {user['name']}!"
