"""
AI-Powered Feature Prioritization Tool
Main Streamlit Application Entry Point
"""

import streamlit as st
from database.db import initialize_database, get_feedback_count, get_feature_count, get_user_features
from auth.auth import (
    initialize_session_state,
    is_logged_in,
    get_current_user,
    login,
    signup,
    logout_user
)
from feedback.feedback_processor import (
    submit_feedback,
    process_csv,
    get_all_feedback,
    get_feedback_stats,
    delete_feedback_item
)
from ai.clustering import (
    run_clustering,
    get_clustering_stats
)
from scoring.rice_scoring import (
    score_feature,
    get_unscored_features,
    get_all_scored_features,
    get_top_features,
    get_scoring_stats,
    get_priority_level,
    get_priority_color
)
from utils.helpers import format_timestamp
import config

# Initialize database on app startup
initialize_database()

# Initialize session state
initialize_session_state()

# Page configuration
st.set_page_config(
    page_title="Feature Prioritization Tool",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# AUTHENTICATION PAGES
# ============================================

def show_auth_page():
    """
    Display login/signup page for unauthenticated users
    """
    # Header
    st.title("🎯 AI-Powered Feature Prioritization Tool")
    st.markdown("---")
    
    # Welcome message
    st.write("""
    ### Welcome!
    Transform user feedback into prioritized features using AI and the RICE framework.
    """)
    
    st.markdown("---")
    
    # Create tabs for Login and Signup
    tab1, tab2 = st.tabs(["🔐 Login", "✨ Sign Up"])
    
    # ===== LOGIN TAB =====
    with tab1:
        st.subheader("Login to Your Account")
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="your@email.com")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            submit_button = st.form_submit_button("Login", use_container_width=True)
            
            if submit_button:
                if email and password:
                    success, message = login(email, password)
                    
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Please enter both email and password")
    
    # ===== SIGNUP TAB =====
    with tab2:
        st.subheader("Create New Account")
        
        with st.form("signup_form"):
            name = st.text_input("Full Name", placeholder="John Doe")
            email = st.text_input("Email", placeholder="your@email.com", key="signup_email")
            password = st.text_input("Password", type="password", placeholder="At least 6 characters", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")
            
            submit_button = st.form_submit_button("Create Account", use_container_width=True)
            
            if submit_button:
                # Validate all fields are filled
                if not all([name, email, password, confirm_password]):
                    st.warning("Please fill in all fields")
                # Check if passwords match
                elif password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    success, message = signup(name, email, password)
                    
                    if success:
                        st.success(message)
                        st.info("👈 Please go to the Login tab to sign in")
                    else:
                        st.error(message)

# ============================================
# MAIN DASHBOARD (LOGGED IN USERS)
# ============================================

def show_dashboard():
    """
    Display main dashboard for authenticated users
    """
    user = get_current_user()
    
    # Sidebar
    with st.sidebar:
        st.title("🎯 Feature Prioritizer")
        st.markdown("---")
        st.write(f"👤 **{user['name']}**")
        st.caption(user['email'])
        st.markdown("---")
        
        # Navigation menu
        st.subheader("Navigation")
        
        # Initialize page state if not exists
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'dashboard'
        
        if st.button("📊 Dashboard", use_container_width=True, 
                     type="primary" if st.session_state.current_page == 'dashboard' else "secondary"):
            st.session_state.current_page = 'dashboard'
            st.rerun()
        
        if st.button("📝 Feedback Collection", use_container_width=True,
                     type="primary" if st.session_state.current_page == 'feedback' else "secondary"):
            st.session_state.current_page = 'feedback'
            st.rerun()
        
        if st.button("🤖 AI Clustering", use_container_width=True,
                     type="primary" if st.session_state.current_page == 'clustering' else "secondary"):
            st.session_state.current_page = 'clustering'
            st.rerun()
        
        if st.button("⭐ Score Features", use_container_width=True,
                     type="primary" if st.session_state.current_page == 'scoring' else "secondary"):
            st.session_state.current_page = 'scoring'
            st.rerun()
        
        st.markdown("---")
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            logout_user()
            st.rerun()
    
    # Route to appropriate page
    if st.session_state.current_page == 'feedback':
        show_feedback_page(user)
    elif st.session_state.current_page == 'clustering':
        show_clustering_page(user)
    elif st.session_state.current_page == 'scoring':
        show_scoring_page(user)
    else:
        show_dashboard_home(user)

def show_dashboard_home(user):
    """
    Display dashboard home page
    """
    st.title("📊 Dashboard")
    st.markdown("---")
    
    # Welcome message
    st.success(f"Welcome, {user['name']}! 👋")
    
    # Get statistics
    feedback_count = get_feedback_count(user['id'])
    feature_count = get_feature_count(user['id'])
    scoring_stats = get_scoring_stats(user['id'])
    scored_count = scoring_stats['scored_count']
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Feedback", feedback_count, help="Number of feedback items collected")
    
    with col2:
        st.metric("Features Identified", feature_count, help="Number of features from AI clustering")
    
    with col3:
        st.metric("Prioritized Features", scored_count, help="Features scored with RICE framework")
    
    st.markdown("---")
    
    # Quick Actions
    st.subheader("Quick Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📝 Add Feedback", use_container_width=True, type="primary"):
            st.session_state.current_page = 'feedback'
            st.rerun()
    
    with col2:
        # Enable clustering button if enough feedback
        can_cluster = feedback_count >= config.MIN_FEEDBACK_FOR_CLUSTERING
        if st.button("🤖 Run AI Clustering", use_container_width=True, disabled=not can_cluster):
            st.session_state.current_page = 'clustering'
            st.rerun()
    
    st.markdown("---")
    
    # Status messages with prioritization workflow
    if feedback_count == 0:
        st.info("👋 **Get Started**: Add your first feedback to begin!")
    elif feedback_count < config.MIN_FEEDBACK_FOR_CLUSTERING:
        st.warning(f"📊 **Collect More Data**: You need at least {config.MIN_FEEDBACK_FOR_CLUSTERING} feedback items for AI clustering. Current: {feedback_count}")
    elif feature_count == 0:
        st.info(f"🤖 **Ready for Clustering**: You have {feedback_count} feedback items. Run AI clustering to identify features!")
    elif scored_count == 0:
        st.info(f"⭐ **Score Features**: {feature_count} features identified. Score them using RICE framework!")
    else:
        st.success(f"✅ **Features Prioritized**: {scored_count}/{feature_count} features scored!")
        
        # Show top 5 features if available
        if scored_count > 0:
            st.markdown("---")
            st.subheader("🎯 Top 5 Recommended Features")
            
            top_features = get_top_features(user['id'], 5)
            
            for idx, feature in enumerate(top_features[:5], 1):
                priority = get_priority_level(feature['rice_score'])
                
                col1, col2, col3 = st.columns([5, 1.5, 1])
                
                with col1:
                    st.write(f"**{idx}. {feature['feature_name']}**")
                
                with col2:
                    st.metric("RICE Score", f"{feature['rice_score']:.1f}")
                
                with col3:
                    if priority == "High":
                        st.success(priority)
                    elif priority == "Medium":
                        st.warning(priority)
                    else:
                        st.error(priority)

def show_feedback_page(user):
    """
    Display feedback collection page
    """
    st.title("📝 Feedback Collection")
    st.markdown("---")
    
    # Tabs for different input methods
    tab1, tab2 = st.tabs(["✍️ Manual Input", "📤 CSV Upload"])
    
    # ===== MANUAL INPUT TAB =====
    with tab1:
        st.subheader("Add Feedback Manually")
        st.write("Enter customer feedback one at a time.")
        
        with st.form("manual_feedback_form"):
            feedback_text = st.text_area(
                "Feedback Text",
                placeholder="Example: The app crashes when I try to upload large files...",
                height=150,
                help="Enter customer feedback (minimum 10 characters)"
            )
            
            submitted = st.form_submit_button("Submit Feedback", use_container_width=True, type="primary")
            
            if submitted:
                if feedback_text:
                    success, message = submit_feedback(user['id'], feedback_text)
                    
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Please enter feedback text")
    
    # ===== CSV UPLOAD TAB =====
    with tab2:
        st.subheader("Upload CSV File")
        st.write("Upload a CSV file with a column named 'feedback' to import multiple entries at once.")
        
        # Show CSV format example
        with st.expander("📋 CSV Format Example"):
            st.code("""feedback
"The app is too slow when loading"
"I love the new dark mode feature"
"Cannot find the export button"
"Great customer support team"
""", language="csv")
            st.caption("Your CSV must have a column named 'feedback' (case-insensitive)")
        
        uploaded_file = st.file_uploader(
            "Choose CSV file",
            type=['csv'],
            help="Upload a CSV file with feedback data"
        )
        
        if uploaded_file is not None:
            if st.button("Import Feedback", type="primary", use_container_width=True):
                with st.spinner("Processing CSV..."):
                    success, message, count = process_csv(user['id'], uploaded_file)
                    
                    if success:
                        st.success(f"✅ {message}")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
    
    st.markdown("---")
    
    # ===== FEEDBACK LIST =====
    st.subheader("Your Feedback")
    
    # Get all feedback
    feedback_list = get_all_feedback(user['id'])
    
    if feedback_list:
        st.write(f"**Total: {len(feedback_list)} feedback items**")
        
        # Display feedback in a nice format
        for idx, feedback in enumerate(feedback_list, 1):
            with st.container():
                col1, col2, col3 = st.columns([6, 1, 0.5])
                
                with col1:
                    st.write(f"**{idx}.** {feedback['feedback_text']}")
                
                with col2:
                    st.caption(format_timestamp(feedback['created_at']))
                
                with col3:
                    # Delete button for each feedback
                    delete_key = f"delete_{feedback['id']}"
                    if st.button("🗑️", key=delete_key, help="Delete this feedback"):
                        success, message = delete_feedback_item(feedback['id'], user['id'])
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                
                st.markdown("---")
    else:
        st.info("No feedback yet. Add your first feedback above!")
    
    # Clustering readiness indicator
    feedback_count = len(feedback_list)
    if feedback_count >= 3:
        st.success(f"✅ Ready for AI Clustering! ({feedback_count} feedback items)")
    elif feedback_count > 0:
        st.warning(f"⚠️ Need {3 - feedback_count} more feedback items for AI clustering")

def show_clustering_page(user):
    """
    Display AI clustering page
    """
    st.title("🤖 AI Clustering")
    st.markdown("---")
    
    # Get clustering statistics
    stats = get_clustering_stats(user['id'])
    
    # Info box
    st.info("""
    **How it works:**
    1. AI analyzes your feedback using natural language processing
    2. Similar feedback items are grouped together
    3. Each group becomes a feature idea
    4. Features are ranked by reach (number of feedback items)
    """)
    
    st.markdown("---")
    
    # Current status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Feedback Items", stats['feedback_count'])
    
    with col2:
        st.metric("Features Identified", stats['feature_count'])
    
    with col3:
        st.metric("Clustering Algorithm", "KMeans")
    
    st.markdown("---")
    
    # Run clustering section
    st.subheader("Run Clustering")
    
    # Check if can run clustering
    if not stats['can_cluster']:
        st.warning(f"⚠️ **Not Ready**: You need at least {stats['min_required']} feedback items to run clustering.")
        st.write(f"Current: {stats['feedback_count']} feedback items")
        
        if st.button("Go to Feedback Collection", type="primary"):
            st.session_state.current_page = 'feedback'
            st.rerun()
    else:
        st.write(f"✅ Ready to cluster {stats['feedback_count']} feedback items into ~{config.DEFAULT_CLUSTER_COUNT} feature groups")
        
        # Configuration info
        with st.expander("ℹ️ Clustering Configuration"):
            st.write(f"**Model:** {config.MODEL_NAME}")
            st.write(f"**Number of Clusters:** {config.DEFAULT_CLUSTER_COUNT}")
            st.write(f"**Minimum Feedback Required:** {config.MIN_FEEDBACK_FOR_CLUSTERING}")
            st.caption("These settings can be changed in config.py")
        
        # Run button
        if st.button("🚀 Run AI Clustering", type="primary", use_container_width=True):
            with st.spinner("🤖 Running AI clustering... This may take a moment..."):
                success, message, feature_count = run_clustering(user['id'])
                
                if success:
                    st.success(f"✅ {message}")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
    
    # Display existing features if any
    if stats['has_features']:
        st.markdown("---")
        st.subheader("Identified Features")
        
        features = get_user_features(user['id'])
        
        if features:
            st.write(f"**Total: {len(features)} features identified**")
            st.caption("Features are sorted by reach (number of feedback items)")
            
            st.markdown("---")
            
            # Display features
            for idx, feature in enumerate(features, 1):
                with st.container():
                    col1, col2, col3 = st.columns([6, 1.5, 1])
                    
                    with col1:
                        st.write(f"**{idx}. {feature['feature_name']}**")
                    
                    with col2:
                        st.metric("Reach", feature['reach'], help="Number of feedback items in this cluster")
                    
                    with col3:
                        st.caption(format_timestamp(feature['created_at']))
                    
                    st.markdown("---")
            
            # Next steps
            st.info("🎯 **Next Step**: Score these features using the RICE framework (Coming in Step 5)")
        else:
            st.info("No features found. Run clustering to identify features from your feedback.")

def show_scoring_page(user):
    """
    Display feature scoring and prioritization page
    """
    st.title("⭐ Feature Scoring & Prioritization")
    st.markdown("---")
    
    # Get statistics
    stats = get_scoring_stats(user['id'])
    
    # Info box
    st.info("""
    **RICE Framework:**
    - **Reach**: Number of feedback items (auto-calculated from clustering)
    - **Impact**: How much this feature will improve the product (1-5 scale)
    - **Confidence**: How sure you are about Impact and Reach (default: 80%)
    - **Effort**: Development complexity (1-5 scale, where 5 = most effort)
    
    **RICE Score** = (Reach × Impact × Confidence) / Effort
    """)
    
    st.markdown("---")
    
    # Statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Features", stats['total_features'])
    
    with col2:
        st.metric("Scored Features", stats['scored_count'])
    
    with col3:
        st.metric("Unscored Features", stats['unscored_count'])
    
    st.markdown("---")
    
    # Check if there are features to score
    if stats['total_features'] == 0:
        st.warning("⚠️ **No Features Found**: Run AI clustering first to identify features.")
        
        if st.button("Go to AI Clustering", type="primary"):
            st.session_state.current_page = 'clustering'
            st.rerun()
    else:
        # Tabs for scoring and priority dashboard
        tab1, tab2 = st.tabs(["📝 Score Features", "🎯 Priority Dashboard"])
        
        # ===== SCORING TAB =====
        with tab1:
            st.subheader("Score Your Features")
            
            unscored_features = get_unscored_features(user['id'])
            
            if not unscored_features:
                st.success("✅ All features have been scored!")
                st.info("💡 You can view the priority dashboard in the next tab.")
            else:
                st.write(f"**{len(unscored_features)} features need scoring:**")
                st.markdown("---")
                
                # Score each feature
                for feature in unscored_features:
                    with st.container():
                        st.write(f"### {feature['feature_name']}")
                        st.caption(f"Reach: {feature['reach']} feedback items")
                        
                        # Create form for this feature
                        with st.form(f"score_form_{feature['id']}"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                impact = st.select_slider(
                                    "Impact (1-5)",
                                    options=[1, 2, 3, 4, 5],
                                    value=3,
                                    help="How much will this improve the product? 1=Minimal, 5=Massive",
                                    key=f"impact_{feature['id']}"
                                )
                            
                            with col2:
                                effort = st.select_slider(
                                    "Effort (1-5)",
                                    options=[1, 2, 3, 4, 5],
                                    value=3,
                                    help="How much work is required? 1=Easy, 5=Very Hard",
                                    key=f"effort_{feature['id']}"
                                )
                            
                            submitted = st.form_submit_button("Calculate RICE Score", use_container_width=True, type="primary")
                            
                            if submitted:
                                success, message, rice_score = score_feature(
                                    feature['id'],
                                    user['id'],
                                    feature['reach'],
                                    impact,
                                    effort,
                                    config.DEFAULT_CONFIDENCE
                                )
                                
                                if success:
                                    st.success(f"✅ {message}")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
                        
                        st.markdown("---")
        
        # ===== PRIORITY DASHBOARD TAB =====
        with tab2:
            st.subheader("Feature Priority Dashboard")
            
            scored_features = get_all_scored_features(user['id'])
            
            if not scored_features:
                st.info("📊 No scored features yet. Score features in the previous tab to see prioritization.")
            else:
                # Top 5 recommendations
                st.success(f"🎯 **Top {min(5, len(scored_features))} Recommended for Next Sprint**")
                
                top_5 = scored_features[:5]
                
                for idx, feature in enumerate(top_5, 1):
                    priority = get_priority_level(feature['rice_score'])
                    
                    with st.container():
                        col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
                        
                        with col1:
                            st.write(f"**{idx}. {feature['feature_name']}**")
                        
                        with col2:
                            st.metric("RICE", f"{feature['rice_score']:.1f}")
                        
                        with col3:
                            st.metric("Reach", feature['reach'])
                        
                        with col4:
                            if priority == "High":
                                st.success(priority)
                            elif priority == "Medium":
                                st.warning(priority)
                            else:
                                st.error(priority)
                        
                        # Show RICE components
                        st.caption(f"Impact: {feature['impact']} | Confidence: {feature['confidence']}% | Effort: {feature['effort']}")
                        
                        st.markdown("---")
                
                # All features table
                if len(scored_features) > 5:
                    st.markdown("---")
                    st.subheader("All Prioritized Features")
                    
                    for idx, feature in enumerate(scored_features[5:], 6):
                        priority = get_priority_level(feature['rice_score'])
                        
                        with st.container():
                            col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
                            
                            with col1:
                                st.write(f"**{idx}. {feature['feature_name']}**")
                            
                            with col2:
                                st.metric("RICE", f"{feature['rice_score']:.1f}")
                            
                            with col3:
                                st.metric("Reach", feature['reach'])
                            
                            with col4:
                                if priority == "High":
                                    st.success(priority)
                                elif priority == "Medium":
                                    st.warning(priority)
                                else:
                                    st.error(priority)
                            
                            st.caption(f"Impact: {feature['impact']} | Confidence: {feature['confidence']}% | Effort: {feature['effort']}")
                            
                            st.markdown("---")
                
                # Summary statistics
                st.markdown("---")
                st.subheader("Summary")
                
                high_priority = len([f for f in scored_features if get_priority_level(f['rice_score']) == "High"])
                medium_priority = len([f for f in scored_features if get_priority_level(f['rice_score']) == "Medium"])
                low_priority = len([f for f in scored_features if get_priority_level(f['rice_score']) == "Low"])
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("High Priority", high_priority, help=f"RICE ≥ {config.RICE_HIGH_THRESHOLD}")
                
                with col2:
                    st.metric("Medium Priority", medium_priority, help=f"RICE ≥ {config.RICE_MEDIUM_THRESHOLD}")
                
                with col3:
                    st.metric("Low Priority", low_priority, help=f"RICE < {config.RICE_MEDIUM_THRESHOLD}")

# ============================================
# MAIN APP ROUTER
# ============================================

def main():
    """
    Main application router
    Routes users to appropriate page based on authentication status
    """
    if is_logged_in():
        show_dashboard()
    else:
        show_auth_page()

if __name__ == "__main__":
    main()
