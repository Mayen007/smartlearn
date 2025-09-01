"""
Firebase Configuration Module for SmartLearn
Handles Firebase Admin SDK initialization and user management
"""

import os
import json
import logging
from functools import wraps
from datetime import datetime

# Import Firebase modules with error handling
try:
    import firebase_admin
    from firebase_admin import credentials, auth, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("⚠️  Firebase Admin SDK not installed. Run: pip install firebase-admin")

from flask import request, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FirebaseManager:
    """Firebase Manager class to handle all Firebase operations"""
    
    def __init__(self):
        self.app = None
        self.db = None
        self.initialized = False
        
    def initialize(self):
        """Initialize Firebase Admin SDK with multiple fallback options"""
        if not FIREBASE_AVAILABLE:
            logger.warning("Firebase Admin SDK not available")
            return False
            
        try:
            # Check if already initialized
            if self.initialized:
                logger.info("Firebase already initialized")
                return True
                
            # Option 1: Service Account Key File
            service_key_path = os.path.join(os.getcwd(), 'serviceAccountKey.json')
            if os.path.exists(service_key_path):
                logger.info("Using service account key file")
                cred = credentials.Certificate(service_key_path)
                self.app = firebase_admin.initialize_app(cred)
                
            # Option 2: Environment Variables
            elif all([
                os.getenv('FIREBASE_PROJECT_ID'),
                os.getenv('FIREBASE_PRIVATE_KEY'),
                os.getenv('FIREBASE_CLIENT_EMAIL')
            ]):
                logger.info("Using environment variables")
                service_account_info = {
                    "type": "service_account",
                    "project_id": os.getenv('FIREBASE_PROJECT_ID'),
                    "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
                    "private_key": os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
                    "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
                    "client_id": os.getenv('FIREBASE_CLIENT_ID'),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
                }
                cred = credentials.Certificate(service_account_info)
                self.app = firebase_admin.initialize_app(cred)
                
            # Option 3: Default credentials (for production environments)
            else:
                logger.info("Using default credentials")
                self.app = firebase_admin.initialize_app()
            
            # Initialize Firestore
            self.db = firestore.client()
            self.initialized = True
            logger.info("✅ Firebase initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Firebase initialization failed: {str(e)}")
            return False
    
    def verify_token(self, token):
        """Verify Firebase ID token"""
        if not self.initialized:
            raise Exception("Firebase not initialized")
            
        try:
            # Remove 'Bearer ' prefix if present
            if token and token.startswith('Bearer '):
                token = token[7:]
                
            decoded_token = auth.verify_id_token(token)
            return decoded_token
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            raise Exception("Invalid token")
    
    def get_user_data(self, uid):
        """Get user data from Firestore"""
        if not self.db:
            return None
            
        try:
            user_ref = self.db.collection('users').document(uid)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                return user_doc.to_dict()
            return None
        except Exception as e:
            logger.error(f"Error getting user data: {str(e)}")
            return None
    
    def create_user_profile(self, uid, email, name, additional_data=None):
        """Create user profile in Firestore"""
        if not self.db:
            return None
            
        try:
            user_data = {
                'uid': uid,
                'email': email,
                'name': name,
                'createdAt': firestore.SERVER_TIMESTAMP,
                'quizScores': [],
                'learningHistory': [],
                'subscriptionStatus': 'free',
                'totalQuizzes': 0,
                'averageScore': 0
            }
            
            if additional_data:
                user_data.update(additional_data)
            
            self.db.collection('users').document(uid).set(user_data, merge=True)
            logger.info(f"User profile created for {email}")
            return user_data
        except Exception as e:
            logger.error(f"Error creating user profile: {str(e)}")
            return None
    
    def save_quiz_result(self, uid, quiz_data):
        """Save quiz result to user's profile"""
        if not self.db:
            return False
            
        try:
            user_ref = self.db.collection('users').document(uid)
            
            # Add timestamp to quiz data
            quiz_data['timestamp'] = firestore.SERVER_TIMESTAMP
            
            # Update user's quiz scores and statistics
            user_ref.update({
                'quizScores': firestore.ArrayUnion([quiz_data]),
                'totalQuizzes': firestore.Increment(1),
                'lastActivity': firestore.SERVER_TIMESTAMP
            })
            
            # Update average score
            self._update_average_score(uid)
            
            logger.info(f"Quiz result saved for user {uid}")
            return True
        except Exception as e:
            logger.error(f"Error saving quiz result: {str(e)}")
            return False
    
    def save_learning_session(self, uid, session_data):
        """Save learning session to user's history"""
        if not self.db:
            return False
            
        try:
            user_ref = self.db.collection('users').document(uid)
            
            # Add timestamp to session data
            session_data['timestamp'] = firestore.SERVER_TIMESTAMP
            
            user_ref.update({
                'learningHistory': firestore.ArrayUnion([session_data]),
                'lastActivity': firestore.SERVER_TIMESTAMP
            })
            
            logger.info(f"Learning session saved for user {uid}")
            return True
        except Exception as e:
            logger.error(f"Error saving learning session: {str(e)}")
            return False
    
    def _update_average_score(self, uid):
        """Update user's average quiz score"""
        try:
            user_data = self.get_user_data(uid)
            if user_data and user_data.get('quizScores'):
                scores = [quiz.get('score', 0) for quiz in user_data['quizScores']]
                if scores:
                    average = sum(scores) / len(scores)
                    self.db.collection('users').document(uid).update({
                        'averageScore': round(average, 2)
                    })
        except Exception as e:
            logger.error(f"Error updating average score: {str(e)}")

# Global Firebase manager instance
firebase_manager = FirebaseManager()

def initialize_firebase():
    """Initialize Firebase - call this from your Flask app"""
    return firebase_manager.initialize()

def require_auth(f):
    """Decorator to require Firebase authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not firebase_manager.initialized:
            return jsonify({'error': 'Firebase not initialized'}), 503
            
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'No authentication token provided'}), 401
        
        try:
            decoded_token = firebase_manager.verify_token(token)
            request.user = decoded_token
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': str(e)}), 401
    
    return decorated_function

def optional_auth(f):
    """Decorator for optional authentication - doesn't fail if no token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        request.user = None
        
        if firebase_manager.initialized:
            token = request.headers.get('Authorization')
            if token:
                try:
                    decoded_token = firebase_manager.verify_token(token)
                    request.user = decoded_token
                except Exception:
                    pass  # Continue without authentication
        
        return f(*args, **kwargs)
    
    return decorated_function

# Convenience functions
def get_user_data(uid):
    return firebase_manager.get_user_data(uid)

def create_user_profile(uid, email, name, additional_data=None):
    return firebase_manager.create_user_profile(uid, email, name, additional_data)

def save_quiz_result(uid, quiz_data):
    return firebase_manager.save_quiz_result(uid, quiz_data)

def save_learning_session(uid, session_data):
    return firebase_manager.save_learning_session(uid, session_data)

def is_firebase_available():
    return firebase_manager.initialized
